"""
Counter example generation using Z3.

This strategy prompts the LLM to produce a Python script that uses the
Python Z3 API to assert constraints representing the failing condition and
produces a concrete model. The LLM must set a variable named
`__z3_cex_result__` to a JSON-serializable dict containing the failing state.
"""

import json
from pathlib import Path
from typing import List, Optional, Set, Tuple

from loguru import logger
from veval import VerusError

from vinv.gen.client import request_conversation_one
from vinv.pipeline.counter_example import CounterExample
from vinv.pipeline.z3_utils import run_z3_script_with_timeout
from vinv.utils import extract_python_code_block


# Validate Z3 model results to ensure only plausible/expected variables are present
def _extract_identifiers_from_rust(code: str) -> Set[str]:
    import re

    if not code:
        return set()

    rust_keywords = {
        # control/flow
        "as",
        "break",
        "const",
        "continue",
        "crate",
        "else",
        "enum",
        "extern",
        "false",
        "fn",
        "for",
        "if",
        "impl",
        "in",
        "let",
        "loop",
        "match",
        "mod",
        "move",
        "mut",
        "pub",
        "ref",
        "return",
        "self",
        "Self",
        "static",
        "struct",
        "super",
        "trait",
        "true",
        "type",
        "unsafe",
        "use",
        "where",
        "while",
        # verus/attributes/syntax often seen
        "requires",
        "ensures",
        "decreases",
        "invariant",
        "opens_invariants_around",
        "forall",
        "exists",
        "ghost",
        "tracked",
        "proof",
        "spec",
        "exec",
        # common types/constructs
        "Vec",
        "Option",
        "Some",
        "None",
        "Result",
        "Ok",
        "Err",
        # numeric/type identifiers
        "i8",
        "i16",
        "i32",
        "i64",
        "i128",
        "u8",
        "u16",
        "u32",
        "u64",
        "u128",
        "usize",
        "isize",
        "int",
        "nat",
        # macros/attrs markers
        "macro_rules",
    }

    # crude identifier scan
    idents = set(re.findall(r"\b[_a-zA-Z][_a-zA-Z0-9]*\b", code))
    return {i for i in idents if i not in rust_keywords}


def _is_vec_ns_key(key: str) -> Tuple[bool, Optional[str]]:
    import re

    m = re.match(r"^__vec__([_a-zA-Z][_a-zA-Z0-9]*)__([0-9]+)$", key)
    if m:
        return True, m.group(1)
    m = re.match(r"^__vec__([_a-zA-Z][_a-zA-Z0-9]*)__len$", key)
    if m:
        return True, m.group(1)
    # legacy patterns
    m = re.match(r"^([_a-zA-Z][_a-zA-Z0-9]*)__([0-9]+)$", key)
    if m:
        return True, m.group(1)
    m = re.match(r"^([_a-zA-Z][_a-zA-Z0-9]*)__len$", key)
    if m:
        return True, m.group(1)
    return False, None


def check_z3_results(
    results: List[dict],
    proof_content: str,
    extracted_loop_function: Optional[str] = None,
) -> Tuple[bool, str, Set[str]]:
    """Minimal check: ensure each assigned variable exists in the proof/loop context.

    Returns (is_valid, reason_message, allowed_names).
    """
    # Build an allowlist of identifiers from the loop (preferred) and entire proof
    allowed_names: Set[str] = set()
    allowed_names |= _extract_identifiers_from_rust(proof_content or "")
    if extracted_loop_function:
        allowed_names |= _extract_identifiers_from_rust(extracted_loop_function)

    invalid_keys: List[str] = []
    for idx, entry in enumerate(results):
        if not isinstance(entry, dict):
            invalid_keys.append(f"result[{idx}] is not a dict")
            continue
        for k in entry.keys():
            if not isinstance(k, str):
                invalid_keys.append(f"[{idx}] non-string key: {k!r}")
                continue
            is_vec_key, base = _is_vec_ns_key(k)
            if k in allowed_names:
                continue
            if is_vec_key and base in allowed_names:
                continue
            invalid_keys.append(f"[{idx}] {k}")

    if invalid_keys:
        reason = (
            "Variables not declared in the proof/loop were found in Z3 assignments: "
            + ", ".join(invalid_keys[:20])
        )
        return False, reason, allowed_names

    return True, "ok", allowed_names


# Post-process: coalesce element-wise names like __vec__arr1__0 into a Rust vec! macro string
def coalesce_vecs(d: dict) -> dict:
    import re as _re
    from collections import defaultdict as _dd

    index_buckets: dict[str, dict[int, object]] = _dd(dict)
    base_lengths: dict[str, int] = {}
    out = dict(d)
    for k, v in list(d.items()):
        # Preferred namespaced pattern: __vec__{base}__{idx}
        m_idx_ns = _re.match(r"^__vec__(.*)__(\d+)$", k)
        if m_idx_ns:
            base, idx = m_idx_ns.group(1), int(m_idx_ns.group(2))
            index_buckets[base][idx] = v
            continue
        # Backward-compatible legacy pattern: {base}_{idx}
        m_idx_legacy = _re.match(r"^(.*)_(\d+)$", k)
        if m_idx_legacy:
            base, idx = m_idx_legacy.group(1), int(m_idx_legacy.group(2))
            index_buckets[base][idx] = v
            continue
        # Preferred namespaced length: __vec__{base}__len
        m_len_ns = _re.match(r"^__vec__(.*)__len$", k)
        if m_len_ns:
            base = m_len_ns.group(1)
            try:
                base_lengths[base] = int(v) if not isinstance(v, bool) else int(v)
            except Exception:
                pass
            continue
        # Legacy length: {base}_len
        m_len_legacy = _re.match(r"^(.*)_len$", k)
        if m_len_legacy:
            base = m_len_legacy.group(1)
            try:
                base_lengths[base] = int(v) if not isinstance(v, bool) else int(v)
            except Exception:
                pass
            continue
    for base, idx_map in index_buckets.items():
        if base in out:
            continue  # already present; don't overwrite
        # Determine indices to use
        if base in base_lengths and base_lengths[base] >= 0:
            idxs = [i for i in range(base_lengths[base]) if i in idx_map]
            if not idxs:
                idxs = sorted(idx_map.keys())
        else:
            idxs = sorted(idx_map.keys())
        # convert values to string
        vals = []
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


def z3_cex_generation(
    failing_proof_file: Path,
    extracted_loop_file: Optional[Path],
    verus_error: VerusError,
    try_dir: Path,
    console_error_msg: str,
    model: str = "gpt-4o",
    num_cex: int = 10,
    z3_exec_timeout_seconds: int = 20,
) -> Optional[List[CounterExample]]:
    """Generate a counter example by asking the LLM to emit a Python Z3 script.

    The LLM should output a Python script that uses `z3` to assert constraints
    and set `__z3_cex_result__` to a dict of concrete variable assignments.
    """
    try:
        try_dir.mkdir(parents=True, exist_ok=True)
        proof_content = failing_proof_file.read_text()
        extracted_loop_function = (
            extracted_loop_file.read_text() if extracted_loop_file else None
        )
        # We'll allow multiple generation attempts so that the LLM can fix
        # issues in generated Z3 scripts (syntax/execution problems or missing
        # counterexample). Each attempt includes feedback about the previous
        # failure to guide the next generation.
        max_generation_attempts = 5
        z3_prompt = create_z3_prompt(
            proof_content=proof_content,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            num_cex=num_cex,
            extracted_loop_function=extracted_loop_function,
        )
        (try_dir / "z3_prompt.txt").write_text(z3_prompt)

        # Ensure Z3 is importable once before attempting generation/execution
        try:
            pass
        except Exception as e:
            logger.error(f"Z3 import failed: {e}")
            return None

        last_error_msg = ""

        # Initialize a persistent conversation so each attempt can build on the last
        base_prompt = z3_prompt
        system_prompt = f"""
You are an expert in Rust/Verus verification and the Python Z3 API.
Produce a Python script that uses the `z3` package to encode the failing
condition described in the Rust/Verus proof and produce a concrete model.
You MUST generate up to {num_cex} distinct satisfying models and collect them.
- You MUST encode the values of ALL variables in the proof/loop/invariant into the final
  results, even if they are not used in the model solving.
"""
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": base_prompt},
        ]

        for gen_attempt in range(1, max_generation_attempts + 1):
            logger.info(
                f"Z3 generation attempt {gen_attempt}/{max_generation_attempts}"
            )

            response_text = request_conversation_one(
                messages,
                model=model,
                max_retry=5,
                temperature=1.0,
                task_id=str(try_dir),
                prompt_type_id="z3_cex_script",
            )

            # Save assistant response for debugging
            (try_dir / f"z3_response_attempt_{gen_attempt}.txt").write_text(
                response_text
            )

            # Append assistant's response to the ongoing conversation
            messages.append({"role": "assistant", "content": response_text})

            # save conversation history
            (try_dir / f"z3_conversation_attempt_{gen_attempt}.json").write_text(
                json.dumps(messages, indent=2)
            )

            z3_code = extract_python_code_block(response_text)
            if not z3_code:
                # If no fenced code block, assume whole response is code
                z3_code = response_text

            # Save the script for this attempt
            script_path = try_dir / f"z3_script_attempt_{gen_attempt}.py"
            script_path.write_text(z3_code)

            # Execute the generated script in a separate process with a timeout
            status, captured, err = run_z3_script_with_timeout(
                z3_code,
                timeout_seconds=z3_exec_timeout_seconds,
                status_key="__z3_cex_status__",
                capture_keys=["__z3_cex_results__"],
            )
            if err is not None:
                last_error_msg = err
                logger.error(last_error_msg)
                # Ask the model to fix the previous script based on the error
                messages.append(
                    {
                        "role": "user",
                        "content": f"Previous attempt failed with error:\n{last_error_msg}\n\n"
                        "Please revise your previous Python Z3 script to fix the issue. "
                        'Ensure it executes without exceptions, sets `__z3_cex_status__` to "sat", "unsat", or "unknown" as appropriate, '
                        "and when SAT, sets `__z3_cex_results__` to a JSON-serializable list of dicts. Return only the corrected Python code.",
                    }
                )
                continue

            # Persist status for debugging
            (try_dir / f"z3_status_attempt_{gen_attempt}.txt").write_text(str(status))

            if isinstance(status, str):
                st = status.strip().lower()
                if st in ("unsat", "unsatisfiable"):
                    last_error_msg = (
                        "Z3 script reported UNSAT/unsatisfiable (no counterexample)"
                    )
                    logger.warning(last_error_msg)
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Previous attempt failed with error:\n{last_error_msg}\n\n"
                            "Please adjust the constraints to make the failing condition satisfiable (prefer minimal constraints). "
                            "Ensure type ranges and vector modeling are respected, then resend ONLY the corrected Python code.",
                        }
                    )
                    continue
                if st == "unknown":
                    last_error_msg = "Z3 script reported unknown satisfiability"
                    logger.warning(last_error_msg)
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Previous attempt failed with error:\n{last_error_msg}\n\n"
                            "Please simplify or adjust the encoding to avoid unknown. Return ONLY the corrected Python code.",
                        }
                    )
                    continue
                # st == 'sat' -> proceed to read result

            # Require list of results
            results = captured.get("__z3_cex_results__")
            if not results:
                last_error_msg = "Z3 script did not set __z3_cex_results__"
                logger.warning(last_error_msg)
                messages.append(
                    {
                        "role": "user",
                        "content": f"Previous attempt failed with error:\n{last_error_msg}\n\n"
                        f"Please modify the script to collect up to {num_cex} of models and assign a JSON-serializable list of dicts to `__z3_cex_results__`. Return ONLY the corrected Python code.",
                    }
                )
                continue

            # Normalize to a list of dicts
            normalized_results: List[dict] = []
            if isinstance(results, list):
                normalized_results = results
            else:
                logger.warning("__z3_cex_results__ is not a list; coercing to list")
                normalized_results = [results]

            normalized_results = [coalesce_vecs(d) for d in normalized_results]

            # if too few results, ask the model to generate more
            if len(normalized_results) < num_cex / 2:
                last_error_msg = f"Only {len(normalized_results)} results found, but {num_cex} are required"
                logger.warning(last_error_msg)
                messages.append(
                    {
                        "role": "user",
                        "content": f"Previous attempt failed with error:\n{last_error_msg}\n\n"
                        f"Please generate more results to meet the requirement of {num_cex}.",
                    }
                )
                continue

            # Ensure serializable
            (try_dir / f"z3_results_attempt_{gen_attempt}.json").write_text(
                json.dumps(normalized_results, indent=2)
            )

            # Build CounterExample
            location = None
            spans = getattr(verus_error, "spans", None)
            if spans:
                try:
                    location = str(spans[0])
                except Exception:
                    location = str(spans)

            cex_list: List[CounterExample] = []
            cex_index = 0
            for state in normalized_results:
                cex = CounterExample(
                    error_type=verus_error.error,
                    failing_state=state,
                    failing_location=location or "unknown",
                    error_message=console_error_msg,
                    cex_index=cex_index,
                    suggested_fix=None,
                )
                cex_list.append(cex)
                cex_index += 1
            (try_dir / f"z3_counter_examples_attempt_{gen_attempt}.json").write_text(
                json.dumps([c.to_dict() for c in cex_list], indent=2)
            )
            # Unified artifacts under cex/
            cex_dir = try_dir / "cex"
            cex_dir.mkdir(parents=True, exist_ok=True)
            unified = []
            for idx, c in enumerate(cex_list):
                d = c.to_dict()
                d["index"] = idx
                unified.append(d)
            (cex_dir / "generated_z3_cex.json").write_text(
                json.dumps(unified, indent=2)
            )
            logger.info(
                f"Generated {len(cex_list)} z3 counter example(s) on attempt {gen_attempt}"
            )
            return cex_list

        # If we reach here, all generation attempts failed
        logger.error(
            f"Failed to generate a valid Z3 counterexample after {max_generation_attempts} attempts for {failing_proof_file}"
        )
        return None

    except Exception as e:
        logger.error(
            f"Failed to generate z3 counter example: {e} for {failing_proof_file}"
        )
        return None


def create_z3_prompt(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    num_cex: int,
    extracted_loop_function: Optional[str] = None,
) -> str:
    """Create a prompt asking the LLM to emit a Python z3 script.

    We require the LLM to produce a Python script (only code) that enumerates up to
    `num_cex` distinct models and sets `__z3_cex_results__` to a JSON-serializable
    list of dicts mapping variable names to concrete values. The script should be
    self-contained and import `z3`.
    """
    focused_error_text = verus_error.get_text()
    full_error_text = console_error_msg
    extracted_loop_section = (
        f"""
To assist in understanding the proof and the target loop, the following is the extracted function where loop invariants are converted into assertions. Use this as a guide to create a Z3 script that reveals the error and generates counterexamples.

Hints for reproducing invariant errors:
1. For "error: invariant not satisfied before loop", please write a Z3 script that finds **reachable** concrete counterexamples that **MUST** falsify the target invariant before the loop.
2. For "error: invariant not satisfied at end of loop body", please write a Z3 script that finds concrete counterexamples (not necessarily reachable) where the the counterexamples **MUST** satisfy the target invariant before the loop and **MUST** satisfy the loop condition, but do not satisfy the target invariant at the end of the loop.

Here is the extracted function with transformed invariants:
```rust
{extracted_loop_function}
```
"""
        if extracted_loop_function
        else ""
    )

    prompt = f"""
Given the following Rust/Verus proof code and the verification error, write a Python script
that uses the Python Z3 API to encode constraints that capture the failing condition and
produce a concrete model (counter example).

Requirements:
- The script must `import z3` and create Z3 variables with appropriate types (Int, Bool, Arrays, etc.).
- The script must assert constraints such that `z3.check()` returns `z3.sat` when the failing
  state is possible.
- Each loop is a separate environment. Please only translate the written invariants/assertions of the loop faithfully, do not add any other constraints elsewhere, e.g., facts from preconditions unless they are explicitly stated in the loop invariants or `#[verifier::loop_isolation(false)]` is specified.
- You MUST enumerate up to {num_cex} distinct satisfying models by adding a blocking clause after each model is found, and collect them.
- The script must assign a JSON-serializable list of dicts to a global variable named `__z3_cex_results__` (each dict maps variable names to concrete values).
- Vectors (naming convention for reconstruction): To avoid name collisions, when you model a Rust Vec like `arr1: Vec<i32>` using element-wise scalars, name them with a namespace as `__vec__arr1__0`, `__vec__arr1__1`, ... (contiguously from 0). Optionally include a concrete scalar `__vec__arr1__len` giving the intended number of elements. You do not need to emit the aggregated `"arr1"` entry; the system will reconstruct `"arr1": "vec![...]"` from your namespaced entries (and `__len` if provided). If you do emit the aggregated entry, it MUST be a STRING like `"vec![1, 2]"`.
- Keep the script minimal and concrete. Use small integer values where possible.
- You MUST encode the values of ALL variables (including arrays or vectors) in the proof/loop/invariant into the final
  results, even if they are not used in the model solving.
- You MUST not assume anything that is not explicitly stated in the loop invariants/assertions/preconditions. If a variable is not explicitly stated in the loop invariants/assertions/preconditions, you MUST NOT assume anything about it even if there are implicit/explicit assignments to it.
- You MUST avoid using Nones in the results.

Practical guidance to avoid UNSAT and runtime errors:
- If a variable like `N`, `len`, or an index is used to size arrays or in Python `range(...)`, do NOT use symbolic Z3 Ints as Python loop bounds; instead, assign a small concrete Int (e.g., `N = z3.IntVal(2)`) and use that concrete value for any Python-side constructs.
- For vectors/arrays, you may model them with explicit small concrete elements instead of Z3 Arrays when convenient, since we only need a single concrete counterexample (e.g., set `a0, a1` as IntVals and relate them, or fix `a = [0, 1]` and express constraints on indices).
- Indices and lengths should be non-negative (>= 0). Avoid expressions that require interpreting a Z3 ArithRef as a Python integer.

Minimize constraints (prefer SAT over faithfulness when ambiguous):
- Choose ONE failing assertion/condition and encode only what is necessary to make it false.
- Use tiny bounded domains (e.g., `N = 2`, indices in {0,1}).
- You may represent `Vec<i32>` internally via namespaced scalar elements `__vec__arr1__0`, `__vec__arr1__1`, ... (optionally include `__vec__arr1__len`). The system will reconstruct an aggregated `"arr1": "vec![...]"` string from these; you do not need to emit it yourself. Legacy names like `arr1_0`/`arr1_len` are also accepted.
- Summarize loops with a few relationships rather than unrolling; avoid quantifiers.
Type modeling and ranges (MANDATORY):
- Model Rust/Verus machine integer types using Z3 Int with explicit range constraints per variable. Add these type-domain constraints in addition to the translated invariants.
- Use the following ranges (assume a 64-bit target for `usize`/`isize`). Prefer exponent form (use 2**k in Python to compute 2^k):
  - bool: use Z3 Bool
  - u8: 0 <= v <= 2^8 - 1
  - u16: 0 <= v <= 2^16 - 1
  - u32: 0 <= v <= 2^32 - 1
  - u64: 0 <= v <= 2^64 - 1
  - u128: 0 <= v <= 2^128 - 1
  - i8: -(2^7) <= v <= 2^7 - 1
  - i16: -(2^15) <= v <= 2^15 - 1
  - i32: -(2^31) <= v <= 2^31 - 1
  - i64: -(2^63) <= v <= 2^63 - 1
  - i128: -(2^127) <= v <= 2^127 - 1
  - usize: 0 <= v <= 2^64 - 1 (64-bit)
  - isize: -(2^63) <= v <= 2^63 - 1 (64-bit)
  - Verus `int`: unbounded Z3 Int (no range restriction)
  - Verus `nat`: Z3 Int with v >= 0
  Note: Do not model modular wraparound; just constrain variables to these ranges unless the invariant explicitly states overflow behavior.

Additional required behavior (to make parsing robust):
- The script MUST set a global variable `__z3_cex_status__` to one of the strings: `"sat"`, `"unsat"`, or `"unknown"`.
- If `__z3_cex_status__ == "sat"`, the script MUST also set `__z3_cex_results__` to a JSON-serializable list of up to {num_cex} concrete variable assignments.
- Ensure that each entry in `__z3_cex_results__` includes all variables (including arrays or vectors) from the proof or target loop, regardless of their involvement in the model solving process.
- If `__z3_cex_status__ == "unsat"`, the script SHOULD NOT set `__z3_cex_result__` (or may set it to an explanatory string/dict). The caller will treat this as no counterexample.
- If `__z3_cex_status__ == "unknown"`, the script indicates it could not determine satisfiability.
- The script should be self-contained, import `z3`, and at the end only set these globals and exit; avoid printing extraneous text.

Rust/Verus proof code:
```rust
{proof_content}
```

{extracted_loop_section}

## Targeted Verification Error:
- **Error Type of the Targeted Error**: {verus_error.error.name}
- **Error Message of the Targeted Error**: {focused_error_text}

Full verifier console output (for context):
```
{full_error_text}
```
At the end, when counterexamples exist, set `__z3_cex_status__ = "sat"` and `__z3_cex_results__ = [ {{"x": 1, "y": 2}} ]` (example, up to {num_cex}). Ensure all values are JSON serializable.
"""
    return prompt
