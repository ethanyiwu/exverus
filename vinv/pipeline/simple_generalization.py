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
from vinv.gen.prompt_utils import render_prompt
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
    cex_validation_backend: str = "v2",
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
            system=render_prompt("pipeline/simple_generalization/system.j2"),
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
    return render_prompt(
        "pipeline/simple_generalization/user.j2",
        proof_content=proof_content,
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        counter_examples=[
            {
                "index": idx,
                "failing_state": cx.failing_state,
                "location": cx.failing_location,
                "why": cx.error_message,
                "suggested_fix": cx.suggested_fix,
            }
            for idx, cx in enumerate(counter_examples or [], start=1)
        ],
        original_proof=original_proof,
        diff=diff,
    )
