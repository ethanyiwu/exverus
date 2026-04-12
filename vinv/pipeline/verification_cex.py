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
                "content": (
                    "You are an expert in Rust/Verus and the Python Z3 API. "
                    "Given an assume/assert-converted program, emit a Python script that finds a model where "
                    "all assumes hold and at least one assert fails, then set required globals."
                ),
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
                feedback = (
                    "Previous attempt failed or incomplete.\n"
                    f"Error/Issue: {last_error_msg}\n\n"
                    f"Previous assistant response (truncated):\n{last_response[-4096:]}\n\n"
                    "Please correct the Python script accordingly."
                )
                base_prompt = feedback + "\n\n" + prompt

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
    return f"""
Given a Rust/Verus proof and an assume/assert-converted variant, write a Python script (only code)
that uses the Python Z3 API to find concrete values at the marker site so that:
1) All assume(...) clauses in the converted code evaluate to TRUE before the step, and
2) After executing the single-step effect encoded in the converted code, at least one assert(...) evaluates to FALSE.

Thinking and targeting (do this mentally, then code):
- Parse the converted code below and list the assert(...) statements that occur AFTER the single-step block (e.g., after push/set and i/n updates). Typical targets include:
  - element-preservation: forall i: 0 <= i < n ==> c[i] == v[i]
  - index and length relations: i <= len, a.len() == N, etc.
- Pick ONE target assert that is plausibly falsifiable by a single step (prefer element-preservation).
- If the target is quantified, instantiate a tiny domain and check a concrete witness (e.g., i = 0) rather than using quantifiers in Z3.

Modeling strategy for a single-step counterexample:
- Use tiny concrete domains and arrays: you may model vectors with a few scalar elements (e.g., v0, v1, c0, c1) or with small Python lists and constrain elements, because we only need one concrete model.
- Enforce all assume(...) clauses exactly as written BEFORE the step (e.g., n != len, v.len() == len, 0 <= n < len+1, forall i < n ==> c[i] == v[i]). For the quantified precondition with n=0, note it holds vacuously.
- Encode the one-step effect on state as in the converted code (e.g., c.push(v[n]); n = n + 1; or equivalent on your small model).
- Then falsify the chosen post-step assert by choosing concrete values, e.g. make c[0] != v[0] when n becomes 1 after the step.

Practical rules:
- Import z3 and use Int/Bool sorts; indices/lengths must be non-negative.
- Avoid using a Z3 symbolic Int in Python range; use tiny concrete integers for bounds (e.g., N = 2, len = 3, n = 0 or 1).
- Keep it minimal and concrete.

Z3 API usage rules (critical):
- Never use Python's if/and/or/not on Z3 BoolRef expressions.
- Compose logic only with z3.And, z3.Or, z3.Not, z3.Implies; add constraints using s.add(...).
- Do not compare BoolRef to True/False; avoid Python truthiness of Z3 objects entirely.
- For conditionals returning expressions, use z3.If(cond, then_expr, else_expr), not Python if.
- Never gate solver.add calls behind Python if using Z3 conditions; build constraints and feed them to the solver.

Absolutely avoid free identifiers and use a witness constant:
- Define a plain Python int witness `i_witness = 0` and only check that index; do NOT reference an undefined `i` anywhere.
- Prefer concrete pre-state like `n0 = 0`, `len_val = 3`, `v = [1,2,3]`, `c = [5,6,7]` (these satisfy all preconditions when n0=0).
- Encode one step to obtain `c_prime` and `n1 = n0 + 1`, then assert `c_prime[i_witness] != v[i_witness]`.

Required globals:
- Set __z3_cex_status__ = "sat" | "unsat" | "unknown".
- If SAT, set __z3_cex_result__ to a JSON-serializable dict mapping ORIGINAL Rust var names to concrete values. For any Rust Vec variables (e.g., `arr1: Vec<i32>`), either:
  - Provide namespaced element-wise scalars `__vec__arr1__0`, `__vec__arr1__1`, ... (optionally `__vec__arr1__len`). The system will reconstruct `"arr1": "vec![...]"` before injection; or
  - Directly provide the aggregated entry `"arr1": "vec![...]"` where the value is a STRING using Rust's vec! macro (preferred when simple). Legacy `arr1_0`/`arr1_len` is also accepted.
- IMPORTANT: Do NOT use f-strings, format(), or any string interpolation. Assign the result using dict(...):
  result = dict(v="[1,2,3]", elem="4", c="[5,6,7]", n="0", len="3")
  __z3_cex_result__ = result
  If you need braces in string content, keep them inside plain strings.

Few-shot Example and Advanced Hints:
To guide your response, study the following example of an input and the ideal output script.

--- Begin Example ---

USER INPUT (Assume/assert-converted code only):

Rust
```rust
fn append_while1(v: &Vec<u64>, elem: u64)
    let mut c = Vec::with_capacity(v.len() + 1);
    let mut n: usize = 0;
    let len: usize = v.len();

    assume(n != len);
    assume(v.len() == len);
    assume(n >= 0);
    assume(n < len + 1);
    // Note: assume(c.len() == n) is missing.
    assume(forall|i: int| (0 <= i && i < n) ==> c[i] == v[i]);

    c.push(v[n]);
    n = n + 1;

    assert(v.len() == len);
    assert(n >= 0);
    assert(n < len + 1);
    assert(forall|i: int| (0 <= i && i < n) ==> c[i] == v[i]);


IDEAL ASSISTANT OUTPUT (The Python script):

Python

from z3 import *

# Goal: Find an initial state where assumes hold but the final assert fails.
# Strategy: Focus on the n=0 case, where the `forall` assume is vacuously true,
# allowing `c` to have arbitrary contents.

__z3_cex_status__ = "unknown"
__z3_cex_result__ =

s = Solver()

# 1. Declare Z3 variables for the program state.
# `c_len` is crucial for modeling the vector's length independently of `n`.
n, len, c_len = Ints('n len c_len')
v = Array('v', IntSort(), IntSort())
c = Array('c', IntSort(), IntSort())

# 2. Concretize the scenario for a quick solution.
# We target the first loop iteration where the `forall` assume is weakest.
s.add(len == 3)
s.add(n == 0)

# 3. Add all preconditions from the `assume` block.
s.add(n != len)
s.add(n >= 0)
s.add(n < len + 1)
s.add(c_len >= 0) # Length must be non-negative

# The `forall` assume is vacuously true for n=0, so it imposes no constraints
# on the initial contents of `c`, which is what allows a counterexample.

# 4. Model the single step. `push` adds to the end of `c` (at index `c_len`).
c_prime = Store(c, c_len, Select(v, n))
n_prime = n + 1

# 5. Add the NEGATION of the target assertion.
# We want to find a case where the final assertion is FALSE.
# The assertion is `forall j in 0..n_prime, c_prime[j] == v[j]`.
# For n=0, n_prime=1, so we only need to check the witness j=0.
j = 0
target_assert = (Select(c_prime, j) == Select(v, j))
s.add(Not(target_assert))

# 6. Solve and format the result.
if s.check() == sat:
    m = s.model()
    # Build the result dictionary with concrete, Rust-like string values.
    len_val = m.evaluate(len).as_long()
    c_len_val = m.evaluate(c_len).as_long()

    # Evaluate arrays to get concrete lists for the output
    v_res = []
    for i in range(len_val):
        val = m.evaluate(Select(v, i))
        v_res.append(val.as_long() if val else 0)

    c_res = []
    for i in range(c_len_val):
        val = m.evaluate(Select(c, i))
        c_res.append(val.as_long() if val else 0)

    n_res = m.evaluate(n).as_long()

    # The user's counterexample used specific values, so we use them for consistency.
    # The actual Z3 result may vary but will have the same logical failure.
    result = dict(
        v=str([1,2,3]),
        elem="4",
        c=str([5,6,7]),
        n=str(n_res),
        len=str(len_val)
    )

    __z3_cex_status__ = "sat"
    __z3_cex_result__ = result
else:
    __z3_cex_status__ = "unsat"

--- End Example ---

Key Principles for Modeling:
Implicit State is Key: A program vector c has both contents (Array) and a length. You MUST model the length with its own Z3 variable (e.g., c_len) unless an assume statement forces it to be equal to another variable (like n).

Model Semantics Precisely: An operation like c.push(v[n]) acts on the vector's end (its current length), which may not be equal to n. Model it as Store(c, c_len, ...).

Exploit Weak Preconditions: A forall over an empty range (e.g., when a loop counter n is 0) is vacuously true. This is the best place to look for counterexamples because the state is less constrained.

Advanced Hints: Modeling Vectors (Vec<T>)
The Two-Part Model: Always model a program Vec<T> with two Z3 variables:

An Array for the contents: v_contents = Array('v', IntSort(), IntSort())

An Int for the length: v_len = Int('v_len')

Translating Operations:

v.len() becomes v_len

v[i] becomes Select(v_contents, i)

v.push(elem) becomes a two-part state update:

v_contents_prime = Store(v_contents, v_len, elem)

v_len_prime = v_len + 1

Advanced Hints: Handling forall Quantifiers
Your primary goal is to find one concrete counterexample, not to create a general proof. SMT solvers are slow with quantifiers. Therefore:

Avoid Z3 ForAll in Assertions: When negating an assert that contains a forall, do not model the ForAll. Instead, pick a single concrete witness index that is likely to fail.

Example: To falsify assert(forall|i: int| 0 <= i < n' ==> c'[i] == v[i]), the best strategy is to check the first new element, or simply index 0. The Z3 constraint should be the much simpler, quantifier-free version:

Python

# Check a single witness index instead of using a slow ForAll
i_witness = 0
s.add(Not(Select(c_prime, i_witness) == Select(v, i_witness)))
Analyze ForAll in Assumptions: For assume statements, the forall is a precondition. The best way to handle it is to find a scenario where it is weak.

Example: For assume(forall|i: int| 0 <= i < n ==> ...), set n = 0 (s.add(n == 0)). This makes the assume vacuously true, placing no constraints on the initial contents of the arrays and giving you the freedom to find a counterexample.

Hint: Avoid Over-Constraining; Focus on Finding "Non-Ideal" States
When generating Z3 constraints to find a counterexample, your primary goal is to exploit weaknesses in the preconditions (assume block), not to "fix" or "idealize" the initial state by adding new, unstated constraints. Bugs and vulnerabilities often hide in states that seem counter-intuitive but are still permitted by the assume clauses.

Core Principles
Don't Assume "Synchronized" or "Ideal" Relationships Between State Variables:

Incorrect Example: In the previous scenario, even if you set s.add(n == 0) to weaken a forall loop, you should never add s.add(c_len == 0) or s.add(c_len == n) on your own initiative.

Reasoning: The program's assume block did not enforce that c.len() must equal n. This "missing constraint" is the core of the vulnerability. By adding this constraint yourself, you are effectively helping the faulty program hide its own bug, which causes Z3 to return unsat and incorrectly imply the code is safe.

Treat an "Unconstrained" Variable as an Opportunity, Not a Problem:

Correct Mindset: When you identify a variable, like c_len, whose value is not strictly limited by the assume block, you should think like a software tester or an attacker: "Can I set this variable to an unexpected but legal value to break the program's logic?"

Correct Example: s.add(c_len >= 1). This constraint explores the possibility that the vector c is non-empty before the loop begins, which is the precise path to finding the counterexample.

Distinguish Between "Strategic Constraints" and "Over-Constraining":

Strategic Constraint: s.add(n == 0) is a good strategic move. It exploits the logical weakness that a precondition like forall|i| 0 <= i < n ==> ... becomes vacuously true when n=0. This maximizes your freedom to find a counterexample using other variables (like the contents of c).

Over-Constraining: s.add(c_len == 0) is a harmful move. It adds a new, powerful assumption that was not required by the code. This assumption closes off the very scenarios where the bug could be found.

Summary
When adding constraints to Z3, strictly adhere to the following rules:

Only add preconditions that are explicitly stated in the code's assume block.

For any variable that is not explicitly constrained, actively explore non-typical, non-ideal, but legal values. This is where vulnerabilities are most likely to be found.

Original Rust/Verus proof (context):
```rust
{proof_content}
```

Assume/assert-converted code (focus near the marker and the post-step asserts):
```rust
{converted_code}
```

Relevant verification output (if any):
```
{verus_analysis_text}
```

Now output ONLY the Python script that sets the required globals.
"""


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
