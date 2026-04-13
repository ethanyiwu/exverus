"""
Verification-oriented counter example generation strategy.

This strategy first converts while-loops into assume/assert forms using the
assume-conversion utilities, then prompts an LLM (GPT-4o) to produce a Python
Z3 script that finds a concrete assignment making all assumes true and some
assert false. It returns a CounterExample compatible with other strategies.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

from vinv.gen.client import request_conversation_one
from vinv.gen.prompt_utils import render_prompt
from vinv.pipeline.assume.run_convert_assume_syn import convert_rust_file_to_string
from vinv.pipeline.counter_example import CounterExample
from vinv.pipeline.z3_utils import run_z3_script_with_timeout
from vinv.utils import extract_python_code_block
from vinv.verus_utils import verify_with_verus

MARKER_PATTERN = r"//\s*place to add variables assignment\. \[(\d+)\]"


def verification_cex_generation(
    failing_proof_file: Path,
    verus_error,
    try_dir: Path,
    console_error_msg: str,
    model: str = "deepseek-reasoner",
    z3_exec_timeout_seconds: int = 20,
) -> Optional[CounterExample]:
    """Generate counterexample using converted assume/assert code and Z3.

    Steps:
    1) Convert input Rust/Verus file to assume/assert form (string only).
    2) Ask LLM for a Python Z3 script that yields concrete assignments via globals.
    3) Execute script in a sandbox with timeout -> get result dict.
    4) Inject a `let (mut ... ) = (...)` assignment into the converted source at
       the marker and optionally verify the injected file (best-effort).
    """
    try:
        try_dir.mkdir(parents=True, exist_ok=True)

        # 1) Convert to assume/assert form and persist a copy for inspection
        converted_code: str = convert_rust_file_to_string(str(failing_proof_file))
        converted_path = try_dir / "converted_assume.rs"
        converted_path.write_text(converted_code)

        # Best-effort: run Verus on the converted code and capture outputs
        verus_analysis_text = ""
        try:
            out_f = try_dir / "converted_input_out.txt"
            err_f = try_dir / "converted_input_err.txt"
            verify_with_verus(
                proof_file=converted_path, stdout_file=out_f, stderr_file=err_f
            )
            try:
                verus_analysis_text = f"{err_f.read_text()}{out_f.read_text()}"
            except Exception:
                verus_analysis_text = ""
            if verus_analysis_text:
                (try_dir / "converted_analysis.txt").write_text(verus_analysis_text)
        except Exception:
            # Environment might not have Verus wired; skip silently
            pass

        # 2) Prompt the LLM to output a Python Z3 script
        proof_content = failing_proof_file.read_text()
        prompt = create_verification_z3_prompt(
            proof_content=proof_content,
            converted_code=converted_code,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            verus_analysis_text=verus_analysis_text,
        )
        (try_dir / "verification_z3_prompt.txt").write_text(prompt)

        messages = [
            {
                "role": "system",
                "content": render_prompt("pipeline/verification_cex/system.j2"),
            },
            {"role": "user", "content": prompt},
        ]

        max_attempts = 5
        last_error_msg = ""
        last_response = ""

        for attempt in range(1, max_attempts + 1):
            logger.info(f"verification z3 attempt {attempt}/{max_attempts}")

            base_prompt = prompt
            if last_error_msg or last_response:
                base_prompt = render_prompt(
                    "pipeline/verification_cex/retry_user.j2",
                    last_error_msg=last_error_msg,
                    last_response=last_response[-4096:],
                    prompt=prompt,
                )

            messages[-1] = {"role": "user", "content": base_prompt}
            response_text = request_conversation_one(
                messages,
                model=model,
                max_retry=5,
                temperature=1.0,
                task_id=str(try_dir),
                prompt_type_id="verification_z3_cex_script",
            )
            (try_dir / f"verification_z3_response_attempt_{attempt}.txt").write_text(
                response_text
            )
            last_response = response_text

            z3_code = extract_python_code_block(response_text) or response_text
            # Sanitize common formatting pitfalls that break dict literals (e.g., f-strings)
            # Hard safeguards: strip f-strings/format/% formatting which break dict literals
            try:
                z3_code = z3_code.replace('f"', '"').replace("f'", "'")
                z3_code = z3_code.replace(".format(", "._noformat(")
                z3_code = z3_code.replace("%(", "_nopct(")
            except Exception:
                pass
            script_path = try_dir / f"verification_z3_script_attempt_{attempt}.py"
            script_path.write_text(z3_code)

            # Reject scripts that still use quantifiers; force a retry with feedback
            if (
                "ForAll(" in z3_code
                or "Exists(" in z3_code
                or "z3.ForAll" in z3_code
                or "z3.Exists" in z3_code
            ):
                last_error_msg = (
                    "Forbidden quantifiers detected (ForAll/Exists). Replace with a concrete witness j = 0 "
                    "or finite instantiation over a tiny set. Do not reference a free 'i'."
                )
                (
                    try_dir / f"verification_z3_reject_quant_attempt_{attempt}.txt"
                ).write_text(last_error_msg)
                continue

            status, captured, err = run_z3_script_with_timeout(
                z3_code,
                timeout_seconds=z3_exec_timeout_seconds,
                status_key="__z3_cex_status__",
                capture_keys=["__z3_cex_result__"],
            )
            if err is not None:
                last_error_msg = err
                logger.error(last_error_msg)
                continue

            try:
                (try_dir / f"verification_z3_status_attempt_{attempt}.txt").write_text(
                    str(status)
                )
            except Exception:
                pass

            st = (status or "").strip().lower() if isinstance(status, str) else None
            if st in ("unsat", "unsatisfiable", "unknown"):
                last_error_msg = f"Z3 script reported {st or 'unknown'}"
                logger.warning(last_error_msg)
                continue

            result = captured.get("__z3_cex_result__")
            if not result or not isinstance(
                result, (dict, list, str, int, float, bool)
            ):
                last_error_msg = "Z3 script did not set a usable __z3_cex_result__"
                logger.warning(last_error_msg)
                continue

            try:
                (try_dir / f"verification_z3_result_attempt_{attempt}.json").write_text(
                    json.dumps(result, indent=2)
                )
            except Exception:
                (try_dir / f"verification_z3_result_attempt_{attempt}.txt").write_text(
                    str(result)
                )

            # Coalesce element-wise names like arr_0, arr_1 into a Rust vec! string "arr": "vec![...]"
            def _coalesce_vecs(d: Dict) -> Dict:
                import re as _re
                from collections import defaultdict as _dd

                index_buckets: Dict[str, Dict[int, object]] = _dd(dict)
                base_lengths: Dict[str, int] = {}
                out = dict(d)
                for k, v in list(d.items()):
                    m_idx = _re.match(r"^(.*)_([0-9]+)$", k)
                    if m_idx:
                        base, idx = m_idx.group(1), int(m_idx.group(2))
                        index_buckets[base][idx] = v
                        continue
                    m_len = _re.match(r"^(.*)_len$", k)
                    if m_len:
                        base = m_len.group(1)
                        try:
                            base_lengths[base] = (
                                int(v) if not isinstance(v, bool) else int(v)
                            )
                        except Exception:
                            pass
                for base, idx_map in index_buckets.items():
                    if base in out:
                        continue
                    if base in base_lengths and base_lengths[base] >= 0:
                        idxs = [i for i in range(base_lengths[base]) if i in idx_map]
                        if not idxs:
                            idxs = sorted(idx_map.keys())
                    else:
                        idxs = sorted(idx_map.keys())
                    vals: list[str] = []
                    for i in idxs:
                        vv = idx_map[i]
                        if isinstance(vv, bool):
                            vals.append("true" if vv else "false")
                        elif isinstance(vv, (int, float)):
                            vals.append(str(vv))
                        else:
                            vals.append(str(vv))
                    out[base] = f"vec![{', '.join(vals)}]"
                return out

            if isinstance(result, dict):
                failing_state: Dict = _coalesce_vecs(result)
            else:
                failing_state = {"result": result}

            injected_code, let_line = inject_assignment_into_converted(
                converted_code, failing_state
            )
            injected_path = try_dir / "verification_injected.rs"
            injected_path.write_text(injected_code)
            if let_line:
                (try_dir / "verification_let_line.txt").write_text(let_line)

            # Best-effort verify the injected file
            try:
                out_file = try_dir / "verification_injected_out.txt"
                err_file = try_dir / "verification_injected_err.txt"
                verify_with_verus(
                    proof_file=injected_path, stdout_file=out_file, stderr_file=err_file
                )
            except Exception:
                pass

            location = None
            spans = getattr(verus_error, "spans", None)
            if spans:
                try:
                    location = str(spans[0])
                except Exception:
                    location = str(spans)

            cex_index = 0
            cex = CounterExample(
                error_type=verus_error.error,
                failing_state=failing_state,
                failing_location=location or "unknown",
                error_message=console_error_msg,
                cex_index=cex_index,
                suggested_fix=(
                    "Insert assignment at marker '[1]' as: " + let_line
                    if let_line
                    else None
                ),
            )
            (
                try_dir / f"verification_counter_example_attempt_{attempt}.json"
            ).write_text(json.dumps(cex.to_dict(), indent=2))
            logger.info(
                f"Generated verification counter example on attempt {attempt}: {cex}"
            )
            cex_index += 1
            return cex

        logger.error(
            f"Failed to generate a valid verification counterexample after {max_attempts} attempts."
        )
        return None

    except Exception as e:
        logger.error(f"verification_cex_generation failed: {e}")
        return None


def create_verification_z3_prompt(
    proof_content: str,
    converted_code: str,
    verus_error,
    console_error_msg: str,
    verus_analysis_text: str,
) -> str:
    """Prompt for producing a Python Z3 script using converted assume/assert code.

    The script must set:
      - __z3_cex_status__ in {"sat","unsat","unknown"}
      - __z3_cex_result__ = { var_name: rust_syntax_string_or_json_value, ... }
    """
    return render_prompt(
        "pipeline/verification_cex/user.j2",
        proof_content=proof_content,
        converted_code=converted_code,
        verus_analysis_text=verus_analysis_text,
    )


def inject_assignment_into_converted(
    converted_code: str, result: Dict
) -> Tuple[str, str]:
    """Replace the line immediately following the marker with a tuple let assignment.

    Returns (new_code, let_line_string). If replacement fails, returns (original, "").
    """
    try:
        lines: List[str] = converted_code.splitlines()
        pattern = re.compile(MARKER_PATTERN)
        produced_let_line = ""
        for i, line in enumerate(lines):
            m = pattern.search(line)
            if not m:
                continue
            # Find next non-empty line that should be the tuple let line
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j >= len(lines):
                break
            m_let = re.search(r"let\s*\(([^)]*)\)\s*=\s*\([^;]*\);", lines[j])
            if not m_let:
                continue
            lhs = m_let.group(1)
            var_names = [v.strip() for v in lhs.split(",") if v.strip()]
            var_names = [v.replace("mut ", "").strip() for v in var_names]

            rhs_values: List[str] = []
            for name in var_names:
                if isinstance(result, dict) and name in result:
                    rhs_values.append(str(result[name]))
                else:
                    rhs_values.append(name)
            indent = (
                re.match(r"([ \t]*)", lines[j]).group(1)
                if re.match(r"([ \t]*)", lines[j])
                else ""
            )
            let_line = f"{indent}let (mut {', mut '.join(var_names)}) = ({', '.join(rhs_values)});"
            lines[j] = let_line
            produced_let_line = let_line.strip()
            break

        return ("\n".join(lines), produced_let_line)
    except Exception:
        return (converted_code, "")
