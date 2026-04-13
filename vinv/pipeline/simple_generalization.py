"""
Simple generalization strategy for Verus verification.

This module provides a straightforward approach to invariant fixing
based on counter examples.
"""

from pathlib import Path
from typing import List, Optional

from loguru import logger
from veval import VerusError

from vinv.gen.client import request_prompt_one
from vinv.pipeline.counter_example import CounterExample
from vinv.utils import extract_rs_code_from_response


def simple_cex_generalization(
    proof_file: Path,
    verus_error: VerusError,
    counter_examples: Optional[List[CounterExample]],
    try_dir: Path,
    console_error_msg: str,
    original_proof_file: Path,
    diff: str,
    model: str = "gpt-4o",
) -> Optional[Path]:
    """
    Generalize from counter examples using a simple, direct approach.

    This strategy focuses on directly fixing invariants based on
    the concrete counter example.
    """
    try:
        proof_content = proof_file.read_text()

        # Create a focused prompt for invariant fixing
        prompt = create_simple_generalization_prompt(
            proof_content=proof_content,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            counter_examples=counter_examples,
            original_proof=original_proof_file.read_text(),
            diff=diff,
        )

        # Save the prompt for debugging
        prompt_file = try_dir / "simple_genz_prompt.txt"
        prompt_file.write_text(prompt)

        # Call LLM
        response_text = request_prompt_one(
            prompt,
            system=(
                "You are an expert in Rust/Verus verification. You are given "
                "counter example(s) and a proof. You need to fix the proof by "
                "strengthening/weakening invariants or assertions."
            ),
            model=model,
            max_retry=5,
            temperature=1.0,
            task_id=str(try_dir),
            prompt_type_id="simple_generalization",
        )

        # Save response for debugging
        response_file = try_dir / "simple_gen_response.txt"
        response_file.write_text(response_text)

        # Extract the fixed code
        fixed_code = extract_rs_code_from_response(response_text)

        if fixed_code:
            # Save the repaired proof
            repaired_file = try_dir / "repaired.rs"
            repaired_file.write_text(fixed_code)
            logger.info(f"Generated simple strengthened proof: {repaired_file}")
            return repaired_file
        else:
            logger.warning("Could not extract fixed code from LLM response")
            return None

    except Exception as e:
        logger.error(f"Failed to generate simple strengthened proof: {e}")
        return None


def create_simple_generalization_prompt(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
    original_proof: str,
    diff: str,
) -> str:
    """Create a focused prompt for direct invariant strengthening."""

    error_type = verus_error.error.name
    error_message = verus_error.get_text()

    # Counter example information
    cex_info = ""
    # Repair guidance
    repair_guidance = ""
    if counter_examples:
        bullets = []
        for idx, cx in enumerate(counter_examples, 1):
            bullets.append(
                f"- Example {idx}: failing_state={cx.failing_state}, location={cx.failing_location}, why='{cx.error_message}', suggested_fix='{cx.suggested_fix}'"
            )
        cex_info = "\n".join(["## Counter Examples Found:"] + bullets)

        # Get specific repair guidance
        repair_guidance = get_repair_guidance(error_type)

    prompt = f"""
# Proof Repair Task

You need to fix the Verus verification failure by modifying invariants, assertions, or decreases clauses as needed.

## Current Proof Code:
```rust
{proof_content}
```

## Targeted Verification Error:
- **Error Type of the Targeted Error**: {error_type}
- **Error Message of the Targeted Error**: {error_message}

Full verifier console output (for context):
```
{console_error_msg}
```
{cex_info}

## Your Task:
{repair_guidance}

Also include the original, unverified proof for reference (note that the repaired proof must not change any execution code, requires/ensures function specifications, etc., of the unverified proof):
{original_proof}

Also include a unified diff showing the delta between the original unverified proof and the current proof under analysis. Use this diff to identify unintended edits to executable code or specifications:
{diff}

## CRITICAL RULES - NEVER MODIFY:
1. Any execution code (logic, control flow, variables, expressions, statements)
2. Function signatures or parameters
3. Requires/ensures function specifications
4. Return values or types
5. NEVER use data type casts (e.g., `i as usize`, `i as int`) in loop invariants

## What you CAN modify:
1. **Loop invariants** - strengthen, weaken, correct, or remove as needed
2. **Decreases clauses** - fix, add, or modify termination arguments
3. **Intermediate assertions** - add, modify, or remove helpful proof steps
4. **Proof annotations** - add, modify, or remove assert statements and lemma calls within proof blocks

## Output Requirement:
Provide the COMPLETE, FULL fixed Rust/Verus code in a single fenced code block:

```rust
// Your complete fixed code here
```

Then provide a brief explanation of what you changed and why.

## Best Practices:
1. **Make minimal changes** - only fix what's needed
2. **Ensure invariants are inductive** - they must be preserved by the loop body
3. **Use concrete bounds** when possible (e.g., `x <= 100` rather than complex expressions)
4. **Remove overly strong invariants** that cannot be maintained
5. **Fix incorrect assertions** that don't actually hold
6. **Ensure decreases clauses actually decrease** on each iteration
7. **Consider whether assertions should be invariants** or vice versa

Fix the proof now:
"""

    return prompt


def get_repair_guidance(error_type: str) -> str:
    """Get specific guidance for repairing invariants/assertions based on error type."""

    guidance_map = {
        "ArithmeticFlow": """
Fix bounds to prevent overflow/underflow. Options:
- **Add bounds**: `x <= MAX_VALUE - increment`, `x >= MIN_VALUE + decrement`
- **Fix division safety**: ensure `divisor != 0` and `divisor > 0` if needed
- **Remove overly restrictive bounds** that can't be maintained
- **Correct wrong bounds** that don't match the actual algorithm
""",
        "InvFailFront": """
The invariant is false when the loop starts. Options:
- **Weaken the invariant** to be true initially
- **Remove incorrect invariants** that don't hold at loop entry
- **Fix wrong conditions** in the invariant
- **Add intermediate assertions** before the loop to establish the invariant
""",
        "InvFailEnd": """
The invariant is not preserved by the loop body. Options:
- **Inductive strengthening** by adding a new invariant that can make the invariants preserved and inductive
- **Weaken overly strong invariants** that can't be maintained
- **Remove incorrect invariants** that don't match the loop logic
- **Fix wrong conditions** that don't account for loop body changes
- **Add intermediate assertions** to help maintain the invariant
""",
        "PostCondFail": """
The postcondition is not satisfied when the function returns. Options:
- **Strengthen loop invariants** to imply the postcondition
- **Remove incorrect invariants** that contradict the postcondition
- **Add bridging assertions** between invariant and postcondition
- **Fix wrong invariant conditions** that don't lead to the postcondition
""",
        "PreCondFail": """
A function call's precondition is not satisfied. Options:
- **Add assertions** before the function call
- **Strengthen invariants** to ensure preconditions hold
- **Remove incorrect assertions** that prevent the precondition
- **Fix wrong conditions** in invariants or assertions
""",
        "AssertFail": """
An assertion is failing. Options:
- **Strengthen invariants** to imply the assertion
- **Remove incorrect assertions** that don't actually hold
- **Fix wrong assertion conditions** that don't match the program logic
- **Replace assertions with weaker conditions** that do hold
- **Add intermediate assertions** to build up to the failing one
""",
    }

    return guidance_map.get(
        error_type,
        """
Analyze the error and modify the relevant invariants or assertions as needed.
Consider strengthening, weakening, fixing, or removing conditions to make the proof work.
""",
    )
