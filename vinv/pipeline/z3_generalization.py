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
                feedback = (
                    "Previous attempt feedback:\n"
                    f"Execution error or issue: {last_error_msg}\n\n"
                    f"Previous assistant response (truncated to last 4KB):\n{last_response[-4096:]}\n\n"
                    "Please correct the Python Z3 script accordingly."
                )
                user_prompt = feedback + "\n\n" + base_prompt

            response_text = request_prompt_one(
                user_prompt,
                system=(
                    "You are an IC3-style inductive generalization expert and "
                    "Python Z3 power user. Your job is to produce a Python "
                    "script (only code) that performs MIC and ctgDown style "
                    "generalization given a failing proof context, then outputs "
                    "the final clause via globals."
                ),
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
            system=(
                "You are an expert in Rust/Verus verification. Your task is to "
                "repair the proof by strengthening or adjusting loop invariants "
                "and/or intermediate assertions using the provided inductive "
                "clause. Do not change executable code or requires/ensures "
                "specifications."
            ),
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

    prompt = f"""
Given the following Rust/Verus proof and a verification error, write a Python script (only code)
that uses the Python Z3 API to perform inductive generalization in the spirit of IC3.

You must implement two key ideas at a high level: MIC (Minimal Inductive Clause) and ctgDown.
You DO NOT need to perfectly model the entire program. Focus only on the failing loop/location
related to the error, capturing a small local transition approximation sufficient to guide
generalization. Be concrete and minimal.

Definitions and goals (high-level):
- Seed cube: a conjunction of literals over relevant state at the failing point. If a concrete
  counterexample or multiple counterexamples are provided, derive the initial cube(s) from them. Otherwise, propose a plausible
  initial clause from the error context.
- MIC (Minimal Inductive Clause): iteratively attempt to drop literals from the current clause.
  For a candidate drop, check relative inductiveness by encoding that the clause holds before the
  transition and fails after the transition. If UNSAT, the drop is safe; keep it dropped. Repeat
  until no more safe drops exist.
- ctgDown (counterexample-to-generalization): when a drop is not safe, produce a witness (model)
  showing the violation and then try to weaken other parts of the clause guided by that witness.
  Iterate between MIC and ctgDown until convergence or a small attempt budget is reached.

What to encode in Z3 (be practical and minimal):
- Declare Z3 variables for the relevant state (Int, Bool, Arrays if needed). Also declare primed
  versions for post-state when needed.
- Translate only the loop invariants and core updates from the loop body (assignments/relations)
  that are necessary to run the inductiveness checks. You can approximate or omit details that are
  irrelevant to the variables in the clause.
- Relative inductiveness check template (conceptual): C(pre) ∧ T(pre, post) ∧ ¬C(post) should be
  UNSAT for C to be inductive relative to T. Use this pattern to test whether dropping a literal
  preserves inductiveness.

Script behavior requirements:
1) The script must `import z3` and construct the necessary Z3 variables and constraints.
2) Implement a small loop that attempts MIC drops on literals of the current clause.
3) When a drop fails (SAT), use the model as ctgDown witness to try weakening other literals or
   adjusting the clause, then continue MIC.
4) Stop when you reach a fixed point or a small attempt budget (e.g., up to 8 tries).
5) At the end, set the following global variables:
   - __z3_genz_status__ = "sat" | "unsat" | "unknown" (use "sat" if you found a clause and checks
     were satisfiable in some steps; use "unsat" if generalization proves unsatisfiable, otherwise
     "unknown" if undecided).
   - __z3_genz_clause__ = a JSON-serializable structure or string representing the final generalized
     clause (e.g., a string like "0 <= i && i <= n" or a list of literal strings). Keep it simple.
   - __z3_genz_notes__ = optional string that summarizes which literals were dropped and any ctgDown
     witnesses used.
6) If a concrete counterexample is provided, use it to form the seed cube; otherwise synthesize a
   reasonable initial clause from the error context.
7) Keep the transition relation minimal and local to the failing loop; do not over-constrain.
8) Do not print extraneous output; only set the globals.
  Additional note: If multiple counterexamples are provided, incorporate all of them when forming
  the seed cube(s) and use them to guide ctgDown so the resulting clause is consistent with all.

Rust/Verus proof code:
```rust
{proof_content}
```

Targeted verification error:
- Error Type: {verus_error.error.name}
- Error Message: {verus_error.get_text()}

Full verifier console output (for context):
```
{console_error_msg}
```

Counterexamples (if any):
```
{cex_info}
```

Implementation hints:
- Prefer small integers and simple linear relations.
- Use helper functions inside the script to evaluate C(pre), C(post), T(pre, post).
- Use a literal list for the clause so you can try removing one literal at a time.
- For ctgDown, inspect the Z3 model returned when a drop is SAT and adjust the clause by
  weakening another literal consistent with the model.
"""
    return prompt


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
    prompt = f"""
# Proof Repair via Inductive Generalization (Injection Stage)

You are given a Rust/Verus proof with a verification failure. A previously executed MIC+ctgDown
procedure (using Z3) produced a generalized clause that should be incorporated into the proof by
strengthening loop invariants or related proof annotations.

Generalized clause to inject (treat as Verus boolean expression or a small set of literals):
```
{generalized_clause}
```

Optional notes/witnesses from ctgDown:
```
{ctg_notes}
```

## Current Proof Code
```rust
{proof_content}
```

## Targeted Verification Error
- Error Type: {verus_error.error.name}
- Error Message: {verus_error.get_text()}

Full verifier console output (for context):
```
{console_error_msg}
```

Original (unverified) proof for reference:
```rust
{original_proof}
```

Unified diff between the above original proof and the current proof under analysis (for spotting unintended changes):
```
{diff}
```

## CRITICAL RULES - NEVER MODIFY
1. Any executable code (logic, control flow, expressions, statements)
2. Function signatures or parameters
3. Requires/ensures function specifications
4. Return values or types
5. Never use data type casts (e.g., `i as usize`, `i as int`) in loop invariants

## What you CAN modify
1. Loop invariants — strengthen/adjust using the generalized clause
2. Decreases clauses — only if needed for termination and consistent with logic
3. Intermediate assertions — add/modify to help establish or preserve invariants
4. Proof annotations — assert statements and lemma calls inside proof blocks

## Your Task
- Identify the relevant loop/location causing the error and strengthen its invariant(s) by
  incorporating the provided generalized clause. Maintain minimal edits and keep semantics intact.
- Ensure the resulting invariants are inductive and help resolve the reported failure.
- Provide the COMPLETE, FULL repaired Rust/Verus code in a single fenced code block:

```rust
// full repaired code here
```

Then briefly explain the changes and why they fix the issue.
"""
    return prompt
