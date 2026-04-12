from pathlib import Path
from typing import List, Optional

from loguru import logger

from vinv.gen.client import request_conversation_one
from vinv.gen.prompt_utils import TEST_TRACE_INFO_PROMPT, read_inv_gen_prompt
from vinv.proof import ProofFile

INVARIANT_MASK = "/* invariant to be inferred */\n"


def disable_no_decreases_clause_check(proof_code: str) -> str:
    """
    Add a #[verifier::exec_allows_no_decreases_clause] to the functions in the proof code.
    Args:
        proof_code (str): The proof code to modify.
    Returns:
        str: The modified proof code with the no decreases clause check disabled.
    """
    lines = proof_code.splitlines()
    modified_lines = []
    for line in lines:
        if line.strip().startswith("fn ") or line.strip().startswith("pub fn "):
            # Add the attribute before the function definition
            modified_lines.append(
                "#[verifier::exec_allows_no_decreases_clause]\n" + line
            )
        else:
            modified_lines.append(line)
    return "\n".join(modified_lines)


def mask_all_invariants(proof: ProofFile) -> str:
    """
    Mask all invariants in the proof file.
    Args:
        proof (ProofFile): The proof file to mask invariants in.
    Returns:
        str: The masked proof code.
    """
    masked_code_lines = []
    invariant_entry_map = proof.parse_invariants()
    if not invariant_entry_map:
        logger.error(f"No invariant entries found in {proof.path}")
        return proof.code

    invariant_entry_list = [
        entry for entries in invariant_entry_map.values() for entry in entries
    ]

    for i in range(len(proof.code_lines)):
        line = proof.code_lines[i]
        if any(entry.invariant_entry_start == i + 1 for entry in invariant_entry_list):
            masked_code_lines.append(INVARIANT_MASK)
        elif any(
            entry.invariant_entry_start < i + 1 <= entry.invariant_entry_end
            for entry in invariant_entry_list
        ):
            pass  # Skip lines that are part of an invariant entry
        else:
            masked_code_lines.append(line)

    return "\n".join(masked_code_lines)


def extract_invariants_from_response(response: str) -> List[str]:
    """
    extract the generated invariants from the LLM response.
    Args:
        response (str): The response from the LLM.
    Returns:
        List[str]: A list of extracted invariant entries.
    """
    invariants_content = response.split("```rust")[1].split("```")[0].strip()

    if not invariants_content:
        raise ValueError("No invariants content found in the response.")

    invariant_lines = invariants_content.splitlines()
    invariant_entry_list = []
    header_idxs = [
        i
        for i, line in enumerate(invariant_lines)
        if line.strip().startswith("# invariant_entry_")
    ]
    if not header_idxs:
        raise ValueError("No invariant entry headers found in the response.")

    for i in range(len(header_idxs)):
        start_idx = header_idxs[i]
        end_idx = (
            header_idxs[i + 1] if i + 1 < len(header_idxs) else len(invariant_lines)
        )
        invariant_entry_code = "\n".join(
            invariant_lines[start_idx + 1 : end_idx]
        ).strip()
        invariant_entry_list.append(invariant_entry_code)

    return invariant_entry_list


def fill_invariant(masked_proof: str, invariants: List[str]) -> str:
    """
    Fill the masked invariants in the proof code with the generated invariants.
    Args:
        masked_proof (str): The proof code with masked invariants.
        invariants (List[str]): The list of generated invariants.
    Returns:
        str: The proof code with filled invariants.
    """
    filled_proof = masked_proof
    for invariant in invariants:
        filled_proof = filled_proof.replace(INVARIANT_MASK, invariant, 1)

    return filled_proof


def mask_and_fill_invariant(
    proof: ProofFile,
    prompt_type: str,
    work_dir: Path,
    mask_all: bool = True,
    model: str = "gpt-4o",
    use_test_trace: bool = False,
    test_driver_file: Optional[Path] = None,
    test_driver_output_file: Optional[Path] = None,
) -> Optional[Path]:
    """
    Mask all invariants in the proof file and fill them with LLM-generated invariants.
    Args:
        proof (ProofFile): The proof file to mask invariants in.
        prompt_type (str): The type of prompt template to use.
        work_dir (Path): The working directory to save the prompt, response, etc.
        mask_all (bool): Whether to mask all invariants or only those that are not already masked.
        model (str): The model to use for the LLM request.
        use_test_trace (bool): Whether to use test trace in the prompt.
        test_driver_file (Optional[Path]): The path to the test driver file.
        test_driver_output_file (Optional[Path]): The path to the test driver output file.
    Returns:
        filled_proof_file (Path): The path to the filled proof file with invariants.
    """
    if not mask_all:
        raise NotImplementedError("Only mask_all=True is supported for now.")
    masked_proof = mask_all_invariants(proof)
    prompt = compile_inv_gen_prompt(
        prompt_type,
        masked_proof,
        use_test_trace=use_test_trace,
        test_driver_file=test_driver_file,
        test_driver_output_file=test_driver_output_file,
    )
    response = request_conversation_one(
        [
            {
                "role": "system",
                "content": "You are an experienced formal language programmer. You are very familiar with Verus, which is a tool for verifying the correctness of code written in Rust.",
            },
            {"role": "user", "content": prompt},
        ],
        model=model,
        temperature=1.0,
        task_id=str(work_dir),
        prompt_type_id=f"inv_gen_{prompt_type}",
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = work_dir / "prompt.txt"
    response_file = work_dir / "response.txt"
    invariants_file = work_dir / "invariants.txt"
    masked_proof_file = work_dir / "masked_proof.rs"
    filled_proof_file = work_dir / "filled_proof.rs"
    gen_status_file = work_dir / "gen_status.txt"

    prompt_file.write_text(prompt)
    response_file.write_text(response)
    masked_proof_file.write_text(masked_proof)

    try:
        invariants = extract_invariants_from_response(response)
    except ValueError as e:
        logger.error(
            f"Error extracting invariants from response: {e} for proof {proof.path}"
        )
        gen_status_file.write_text("invariant_extraction_failed")
        return None
    if not invariants:
        logger.error(f"No invariants generated for {proof.path}")
        gen_status_file.write_text("no_invariants_generated")
        return None

    num_invariant_placeholders = masked_proof.count(INVARIANT_MASK)
    if len(invariants) != num_invariant_placeholders:
        logger.warning(
            f"Number of generated invariants ({len(invariants)}) does not match the number of invariant entries in the proof ({len(proof.parse_invariants())}) for {work_dir}."
        )
        gen_status_file.write_text("invariant_count_mismatch")
        return None
    else:
        gen_status_file.write_text("success")
        filled_proof = fill_invariant(masked_proof, invariants)
        filled_proof = disable_no_decreases_clause_check(filled_proof)
        filled_proof_file.write_text(filled_proof)
        logger.info(
            f"Filled proof with invariants saved to {filled_proof_file} for {proof.path}"
        )
    invariants_content = ""
    for i, invariant in enumerate(invariants):
        invariants_content += f"# invariant_entry_{i}\n{invariant}\n\n"

    invariants_file.write_text(invariants_content)
    return filled_proof_file


def compile_inv_gen_prompt(
    prompt_type: str,
    masked_proof: str,
    use_test_trace: bool = False,
    test_driver_file: Optional[Path] = None,
    test_driver_output_file: Optional[Path] = None,
) -> str:
    """
    Compile the invariant generation prompt with the masked code.
    Args:
        prompt_type (str): The prompt_type to use.
        masked_code (str): The masked code to include in the prompt.
        use_test_trace (bool): Whether to use test trace in the prompt.
        test_driver_file (Optional[Path]): The path to the test driver file.
        test_driver_output_file (Optional[Path]): The path to the test driver output file.
    Returns:
        str: The compiled invariant generation prompt.
    """
    inv_gen_prompt = read_inv_gen_prompt(prompt_type)
    if use_test_trace:
        inv_gen_prompt = inv_gen_prompt.replace(
            "<test_trace_info>", TEST_TRACE_INFO_PROMPT
        )
        assert (
            test_driver_file.exists() and test_driver_output_file.exists()
        ), f"Test driver file {test_driver_file} or test driver output file {test_driver_output_file} does not exist."
        inv_gen_prompt = inv_gen_prompt.replace(
            "<test_driver_code>",
            test_driver_file.read_text(),
        ).replace(
            "<execution_output>",
            test_driver_output_file.read_text(),
        )

    else:
        inv_gen_prompt = inv_gen_prompt.replace("<test_trace_info>", "")

    return inv_gen_prompt.replace("<proof_missing_invariants>", masked_proof)
