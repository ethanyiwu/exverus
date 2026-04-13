"""
Simple counter example generation strategy for Verus verification.

This module provides a straightforward approach to counter example generation
that directly prompts the LLM to find concrete failing states based on the
verification error.
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from loguru import logger
from veval import VerusError

# Note: We create our own simple prompt instead of using the complex IC3 prompt
from vinv.gen.client import request_prompt_one
from vinv.pipeline.counter_example import CounterExample


def simple_cex_generation(
    failing_proof_file: Path,
    extracted_loop_file: Optional[Path],
    verus_error: VerusError,
    try_dir: Path,
    console_error_msg: str,
    model: str = "gpt-4o",
    num_cex: int = 10,
) -> Optional[List[CounterExample]]:
    """
    Generate counter examples using a simple, direct LLM prompting approach.

    This strategy focuses on finding concrete failing states in 1-2 steps.
    """
    try:
        proof_content = failing_proof_file.read_text()

        # Create a simple, focused prompt for counter example generation
        prompt = create_simple_cex_prompt(
            proof_content=proof_content,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            num_cex=num_cex,
        )

        # Save the prompt for debugging
        prompt_file = try_dir / "simple_cex_prompt.txt"
        prompt_file.write_text(prompt)

        # Call LLM
        response_text = request_prompt_one(
            prompt,
            system=(
                "You are an expert in Rust/Verus verification. Find concrete "
                "counter examples that demonstrate why verification fails."
            ),
            model=model,
            max_retry=5,
            temperature=1.0,
            task_id=str(try_dir),
            prompt_type_id="simple_cex",
        )

        # Save response for debugging
        response_file = try_dir / "simple_cex_response.txt"
        response_file.write_text(response_text)

        # Parse the response to extract counter examples (up to num_cex)
        counter_examples = parse_simple_cex_responses(
            response_text, verus_error, console_error_msg, limit=num_cex
        )

        if counter_examples:
            # Save counter examples details
            cex_file = try_dir / "simple_counter_examples.json"
            cex_file.write_text(
                json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
            )
            # Unified artifacts under cex/
            cex_dir = try_dir / "cex"
            cex_dir.mkdir(parents=True, exist_ok=True)
            unified = []
            for idx, c in enumerate(counter_examples):
                d = c.to_dict()
                d["index"] = idx
                unified.append(d)
            (cex_dir / "generated_simple_cex.json").write_text(
                json.dumps(unified, indent=2)
            )
            logger.info(f"Generated {len(counter_examples)} simple counter example(s)")

        return counter_examples if counter_examples else None

    except Exception as e:
        logger.error(f"Failed to generate simple counter example: {e}")
        return None


def create_simple_cex_prompt(
    proof_content: str, verus_error: VerusError, console_error_msg: str, num_cex: int
) -> str:
    """Create a focused prompt for direct counter example generation."""

    error_type = verus_error.error.name
    focused_error_message = verus_error.get_text()
    full_error_message = console_error_msg

    # Get error-specific guidance
    error_guidance = get_error_specific_guidance(error_type)

    prompt = f"""
# Counter Example Generation Task

You are analyzing a Verus verification failure and need to find up to {num_cex} concrete counter examples that demonstrate why the proof fails.

## Current Proof Code:
```rust
{proof_content}
```

## Targeted Verification Error:
- **Error Type of the Targeted Error**: {error_type}
- **Error Message of the Targeted Error**: {focused_error_message}

Full verifier console output (for context):
```
{full_error_message}
```

## Your Task:
{error_guidance}

## Output Format:
Provide up to {num_cex} counterexamples by REPEATING the following block for each distinct case (use different values):

```
COUNTER_EXAMPLE:
failing_state: {{
  // Concrete variable values that cause the failure
  // Example: "x": 5, "y": 10, "arr_len": 3
}}
location: "specific location in code where failure occurs"
explanation: "brief explanation of why this state causes failure"
suggested_fix: "what needs to be strengthened/fixed/deleted"
```

## Requirements:
1. **Be Concrete**: Provide specific numeric values, not ranges or symbolic expressions
2. **Be Minimal**: Find the simplest cases that demonstrate the failure
3. **Be Distinct**: Provide different failing states (avoid duplicates)
4. **Be Precise**: The failing state should directly relate to the error type
5. **Focus on Root Cause**: Identify the fundamental issue, not just symptoms
6. **Be Disciplined**: Do not suggest modifying any execution code or pre/post conditions

Vector/array representation (MANDATORY for this task):
- When the failing state contains a Rust Vec (e.g., `arr1: Vec<i32>`), represent it in the failing_state as a Rust expression string using the vec! macro, for example:
  - "arr1": "vec![1, 2, 3]"
- Do NOT output Python/Z3 arrays or JSON arrays for Vecs. Always use a quoted Rust expression string `"vec![...]"` so it can be injected directly into the Rust harness.

Find the counter example now:
"""

    # TODO: remove "explanation" and "suggested_fix" section for fair comparison

    return prompt


def get_error_specific_guidance(error_type: str) -> str:
    """Get specific guidance based on the verification error type."""

    guidance_map = {
        "ArithmeticFlow": """
Find concrete values that cause integer overflow, underflow, or division by zero.
Look for operations like addition, subtraction, multiplication, or division that could exceed bounds.
""",
        "InvFailFront": """
Find concrete values at loop entry where the invariant should hold but doesn't.
The invariant is expected to be true when the loop starts, but your counter example should show it's false.
""",
        "InvFailEnd": """
Find concrete values where the loop body preserves all conditions except the invariant.
The loop body executes correctly but fails to maintain the invariant for the next iteration.
""",
        "PostCondFail": """
Find concrete values where the function executes without errors but the postcondition is false.
All preconditions are satisfied, the function completes, but the promised result doesn't hold.
""",
        "PreCondFail": """
Find concrete values where a function call's precondition is not satisfied.
Look for function calls where the required input conditions are violated.
""",
        "AssertFail": """
Find concrete values that make an assertion statement false.
The assertion might be incorrect or redundant. Find the concrete values that make the assertion false.
""",
        "PreCondFailVecLen": """
Find concrete values that make a vector length check fail.
Maybe the bound of the vector is missing or incorrect. Find the concrete values that make the vector length precondition fail, e.g., out of bounds.
""",
    }

    return guidance_map.get(
        error_type,
        """
Find concrete values that demonstrate why the verification fails.
Look at the error message for clues about what condition is being violated.
""",
    )


def parse_simple_cex_responses(
    response_text: str,
    verus_error: VerusError,
    console_error_msg: str,
    limit: int,
) -> List[CounterExample]:
    """Parse the LLM response to extract up to `limit` counter examples."""

    results: List[CounterExample] = []
    cex_index = 0
    try:
        # Find all COUNTER_EXAMPLE blocks
        block_pattern = (
            r"COUNTER_EXAMPLE\s*:\s*\n([\s\S]*?)(?=\n\s*COUNTER_EXAMPLE\s*:|\n```|\Z)"
        )
        for m in re.finditer(block_pattern, response_text):
            if len(results) >= limit:
                break
            cex_content = m.group(1).strip()

            failing_state = extract_failing_state(cex_content)
            location = extract_field(cex_content, "location")
            suggested_fix = extract_field(cex_content, "suggested_fix")
            if failing_state:
                results.append(
                    CounterExample(
                        error_type=verus_error.error,
                        failing_state=failing_state,
                        failing_location=location or "unknown",
                        error_message=console_error_msg,
                        cex_index=cex_index,
                        suggested_fix=suggested_fix or "strengthen invariant",
                    )
                )
                cex_index += 1

    except Exception as e:
        logger.error(f"Failed to parse simple counter examples: {e}")

    return results


def extract_failing_state(content: str) -> Optional[dict]:
    """Extract the failing_state dictionary from the response."""

    # Look for failing_state: { ... } with more flexible matching
    state_pattern = r"failing_state:\s*\{(.*?)\n\s*\}"
    state_match = re.search(state_pattern, content, re.DOTALL)

    if not state_match:
        return None

    state_content = state_match.group(1).strip()

    # Parse the key-value pairs line by line for better control
    state = {}

    # Split into lines and process each key-value pair
    lines = state_content.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        # Remove inline comments
        line = re.sub(r"\s*//.*$", "", line)
        line = line.strip().rstrip(",")

        # Match key-value pairs
        match = re.match(r'"([^"]+)":\s*(.+)', line)
        if not match:
            continue

        key, value = match.groups()
        value = value.strip()

        # Handle different value types
        if value.startswith("[") and value.endswith("]"):
            # Array - extract numbers or keep as string representation
            try:
                # Simple array parsing for numbers
                array_content = value[1:-1]
                if array_content.strip():
                    numbers = [int(x.strip()) for x in array_content.split(",")]
                    state[key] = numbers
                else:
                    state[key] = []
            except ValueError:
                # Keep as string if can't parse as numbers
                state[key] = value
        elif value.startswith('"') and value.endswith('"'):
            # String value
            state[key] = value[1:-1]
        else:
            # Try to parse as number
            try:
                if "." in value:
                    state[key] = float(value)
                else:
                    state[key] = int(value)
            except ValueError:
                # Keep as string if not a number
                state[key] = value.strip('"')

    return state if state else None


def extract_field(content: str, field_name: str) -> Optional[str]:
    """Extract a specific field from the counter example content."""

    # Try to find field_name: followed by content until the next field or end
    # Handle both quoted and unquoted content
    patterns = [
        # Pattern 1: Quoted content (supports nested quotes)
        rf'{field_name}:\s*"((?:[^"\\]|\\.)*)"',
        rf"{field_name}:\s*'((?:[^'\\]|\\.)*)'",
        # Pattern 2: Unquoted content until next field or end
        rf"{field_name}:\s*(.*?)(?=\n\w+:|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            result = match.group(1).strip()
            return result

    return None
