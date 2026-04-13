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
from vinv.gen.prompt_utils import render_prompt
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
            system=render_prompt("pipeline/simple_cex/system.j2"),
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
    return render_prompt(
        "pipeline/simple_cex/user.j2",
        proof_content=proof_content,
        error_type=verus_error.error.name,
        focused_error_message=verus_error.get_text(),
        full_error_message=console_error_msg,
        num_cex=num_cex,
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
