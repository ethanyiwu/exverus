"""
Z3-driven inductive generalization (genz) using MIC and ctgDown, orchestrated by an LLM.

This strategy asks the LLM to role-play an IC3 inductive generalization expert. It produces
small Python Z3 scripts to iteratively generalize from a seed cube (e.g., from a counterexample)
using the MIC algorithm and ctgDown. We run those scripts locally, capture a generalized
invariant clause, and then ask the LLM (as a Verus proof engineer) to inject the clause into
the Rust/Verus proof by strengthening the relevant loop invariants.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from loguru import logger
from veval import VerusError

from vinv.gen.client import request_prompt_one
from vinv.gen.prompt_utils import render_prompt
from vinv.pipeline.counter_example import CounterExample
from vinv.pipeline.simple_generalization import simple_cex_generalization
from vinv.pipeline.z3_utils import run_z3_script_with_timeout
from vinv.utils import extract_python_code_block, extract_rs_code_from_response


def z3_cex_generalization(
    proof_file: Path,
    verus_error: VerusError,
    counter_examples: Optional[List[CounterExample]],
    try_dir: Path,
    console_error_msg: str,
    original_proof_file: Path,
    diff: str,
    model: str = "gpt-4o",
    cex_validation_backend: str = "v2",
    z3_exec_timeout_seconds: int = 20,
) -> Optional[Path]:
    """
    Use an LLM + Python Z3 to perform MIC + ctgDown style inductive generalization, then
    inject the resulting clause into the Verus proof by fixing invariants.

    Returns a path to the repaired proof (repaired.rs) on success; otherwise None.
    """
    try:
        try_dir.mkdir(parents=True, exist_ok=True)
        proof_content = proof_file.read_text()

        # Ensure Z3 is importable prior to script execution attempts
        try:
            pass  # type: ignore
        except Exception as e:
            logger.error(f"Z3 import failed: {e}")
            return None

        # Stage A/B: Ask LLM to iteratively run MIC and ctgDown via a Python Z3 script.
        base_prompt = create_mic_ctg_z3_prompt(
            proof_content=proof_content,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            counter_examples=counter_examples,
        )
        (try_dir / "z3_genz_prompt.txt").write_text(base_prompt)

        max_genz_attempts = 5
        last_error_msg = ""
        last_response = ""
        selected_clause: Optional[str] = None
        selected_notes: Optional[str] = None

        for genz_attempt in range(1, max_genz_attempts + 1):
            logger.info(f"Z3 genz attempt {genz_attempt}/{max_genz_attempts}")

            user_prompt = base_prompt
            if last_error_msg or last_response:
                user_prompt = render_prompt(
                    "pipeline/z3_generalization/script_retry_user.j2",
                    last_error_msg=last_error_msg,
                    last_response=last_response[-4096:],
                    base_prompt=base_prompt,
                )

            response_text = request_prompt_one(
                user_prompt,
                system=render_prompt("pipeline/z3_generalization/script_system.j2"),
                model=model,
                max_retry=5,
                temperature=1.0,
                task_id=str(try_dir),
                prompt_type_id="z3_genz_script",
            )
            (try_dir / f"z3_genz_response_attempt_{genz_attempt}.txt").write_text(
                response_text
            )
            last_response = response_text

            z3_code = extract_python_code_block(response_text)
            if not z3_code:
                # If no fenced code block, assume whole response is code
                z3_code = response_text

            script_path = try_dir / f"z3_genz_script_attempt_{genz_attempt}.py"
            script_path.write_text(z3_code)

            # Execute the generated script in a separate process with a timeout
            status, captured, err = run_z3_script_with_timeout(
                z3_code,
                timeout_seconds=z3_exec_timeout_seconds,
                status_key="__z3_genz_status__",
                capture_keys=["__z3_genz_clause__", "__z3_genz_notes__"],
            )
            if err is not None:
                last_error_msg = err
                logger.error(last_error_msg)
                continue
            clause = captured.get("__z3_genz_clause__")
            notes = captured.get("__z3_genz_notes__")

            # Persist any results for debugging
            try:
                (try_dir / f"z3_genz_status_attempt_{genz_attempt}.txt").write_text(
                    str(status)
                )
            except Exception:
                pass
            try:
                if clause is not None:
                    (
                        try_dir / f"z3_genz_clause_attempt_{genz_attempt}.json"
                    ).write_text(json.dumps(clause, indent=2))
            except Exception:
                try:
                    (try_dir / f"z3_genz_clause_attempt_{genz_attempt}.txt").write_text(
                        str(clause)
                    )
                except Exception:
                    pass
            try:
                if notes is not None:
                    (try_dir / f"z3_genz_notes_attempt_{genz_attempt}.txt").write_text(
                        str(notes)
                    )
            except Exception:
                pass

            # Validate and capture the clause
            st = str(status).strip().lower() if status is not None else ""
            if st in ("sat", "unsat", "unknown") and clause:
                # We accept any non-empty clause from the LLM-driven script. Treat as opaque string/JSON.
                try:
                    # If clause is JSON-like list/dict, store JSON text; otherwise str()
                    if isinstance(clause, (dict, list)):
                        selected_clause = json.dumps(clause)
                    else:
                        selected_clause = str(clause)
                except Exception:
                    selected_clause = str(clause)
                selected_notes = str(notes) if notes is not None else None
                break

            last_error_msg = "Script did not set valid __z3_genz_status__ in {sat,unsat,unknown} or provided empty clause."

        # Fallback if we did not obtain any clause
        if not selected_clause:
            logger.warning(
                "Z3 genz failed to produce a usable clause; falling back to simple generalization."
            )
            return simple_cex_generalization(
                proof_file=proof_file,
                verus_error=verus_error,
                counter_examples=counter_examples,
                try_dir=try_dir,
                console_error_msg=console_error_msg,
                original_proof_file=original_proof_file,
                diff=diff,
                model=model,
                cex_validation_backend=cex_validation_backend,
            )

        # Stage C: Ask LLM to inject/strengthen invariants with the obtained clause
        verus_prompt = create_verus_injection_prompt(
            proof_content=proof_content,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            original_proof=original_proof_file.read_text(),
            diff=diff,
            generalized_clause=selected_clause,
            ctg_notes=selected_notes or "",
        )
        (try_dir / "z3_genz_injection_prompt.txt").write_text(verus_prompt)

        response_text2 = request_prompt_one(
            verus_prompt,
            system=render_prompt("pipeline/z3_generalization/injection_system.j2"),
            model=model,
            max_retry=5,
            temperature=1.0,
            task_id=str(try_dir),
            prompt_type_id="verus_injection",
        )
        (try_dir / "z3_genz_injection_response.txt").write_text(response_text2)

        fixed_code = extract_rs_code_from_response(response_text2)
        if not fixed_code:
            # As a fallback, if the assistant returned code without fences, just take it raw
            fixed_code = response_text2

        repaired_file = try_dir / "repaired.rs"
        repaired_file.write_text(fixed_code)
        logger.info(f"Generated z3 genz strengthened proof: {repaired_file}")
        return repaired_file

    except Exception as e:
        logger.error(f"Failed to perform z3 generalization: {e}")
        return None


def create_mic_ctg_z3_prompt(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
) -> str:
    """
    Create a detailed prompt instructing the LLM to emit a Python Z3 script that performs
    MIC and ctgDown style inductive generalization and sets result globals.
    """
    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)
    return render_prompt(
        "pipeline/z3_generalization/script_user.j2",
        proof_content=proof_content,
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        cex_info=cex_info,
    )


def create_verus_injection_prompt(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    original_proof: str,
    diff: str,
    generalized_clause: str,
    ctg_notes: str,
) -> str:
    """
    Create a prompt to inject the generalized clause into the Verus proof by fixing
    loop invariants. We enforce strict editing rules to avoid changing executable code/specs.
    """
    return render_prompt(
        "pipeline/z3_generalization/injection_user.j2",
        generalized_clause=generalized_clause,
        ctg_notes=ctg_notes,
        proof_content=proof_content,
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        original_proof=original_proof,
        diff=diff,
    )
