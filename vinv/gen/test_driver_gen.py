import subprocess
from pathlib import Path
from typing import Literal, Optional

from fire import Fire
from loguru import logger

from vinv.data.cherrypick import get_all_obfs_proofs, get_all_vb_proofs
from vinv.gen.client import request_conversation_one
from vinv.gen.prompt_utils import (
    VERUS_SYSTEM_PROMPT,
    count_tokens,
    read_test_driver_gen_prompt,
    write_conversation_file,
)
from vinv.proof import FuncType, ProofFile
from vinv.utils import extract_rs_code_from_response, get_result_dir

OUTPUT_MAX_TOKENS = 40960  # Maximum tokens for the test driver output

"""
Script to generate a test driver from a proof file. The script takes a raw rust
program (deghosted from a proof file) along with the gt proof file itself, and
generates a test driver that can produce some test cases and execution traces.
2 test driver modes are supported:
1. llm-generated, hardcoded concrete test cases
2. llm-generated, test driver accepting user input from standard input

The LLM will insert logging statements in the test driver to print the
execution trace of the program, e.g., the values of variables at each step, the
existing predicates in the invariants or asserts, or the predicates that are
useful for verification but not in the invariants, etc.
"""


def extract_specs_from_proof(proof: ProofFile) -> str:
    """
    Extract specifications from the proof file.
    Args:
        proof (ProofFile): The proof file object containing the proof.
    Returns:
        str: The extracted specifications as a string.
    """
    extracted_specs = ""
    cnt = 0
    for func_id in proof.func_ids:
        func_type = proof.func_type_dict[func_id]
        if func_type != FuncType.NORMAL:
            continue
        cnt += 1
        spec_entry = proof.parse_spec_entry_for_func_id(func_id)
        extracted_specs += f"Function {func_id.split('_')[0]} specifications:\n"
        extracted_specs += f"{spec_entry.spec_code}\n\n"
    if cnt != 1:
        logger.warning(
            f"Expected exactly one function with specifications, but found \
                {cnt} in {proof.path}"
        )
    return extracted_specs


def compile_test_driver_prompt(
    raw_program_file: Path,
    extracted_specs: str,
    # gt_proof_file: Path,
    num_tests: int = 5,
    unverified_or_buggy_proof_file: Optional[Path] = None,
    verus_feedback: Optional[str] = None,
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
) -> str:
    """
    Compile the test driver prompt based on the specified type and files.
    Args:
        raw_program_file (Path): The path to the raw Rust program file.
        extracted_specs (str): The extracted specifications from the proof file.
        # gt_proof_file (Path): The path to the ground truth proof file.
        unverified_or_buggy_proof_file (Optional[Path]): The path to the raw or buggy
        proof file, if available.
        verus_feedback (Optional[str]): Feedback from Verus verification of the
        buggy proof, if available.
        test_driver_mode (Literal["hardcoded", "stdin"]): The mode of the test
        driver.
    Returns:
        str: The compiled prompt string.
    """
    prompt = read_test_driver_gen_prompt(test_driver_mode)

    prompt = prompt.replace(
        "<num_tests>",
        str(num_tests),
    )
    prompt = prompt.replace(
        "<raw_program>",
        raw_program_file.read_text().strip(),
    )
    prompt = prompt.replace(
        "<extracted_specs>",
        extracted_specs.strip(),
    )

    return prompt


def llm_instrument(
    test_driver_dir: Path,
    raw_program_file: Path,
    gt_proof: ProofFile,
    model: str = "gpt-4o",
    num_tests: int = 5,
    unverified_or_buggy_proof_file: Optional[Path] = None,
    verus_feedback: Optional[str] = None,
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
    max_retry: int = 5,
):
    """
    Generate a test driver for the given raw program file using the specified LLM model.
    Args:
        test_driver_dir (Path): The directory where the test driver will be saved.
        raw_program_file (Path): The path to the raw Rust program file.
        gt_proof (ProofFile): The ground truth proof file object containing the proof.
        model (str): The LLM model to use for generation.
        num_tests (int): The number of test cases to generate.
        unverified_or_buggy_proof_file (Optional[Path]): The path to the raw or buggy
        proof file, if available.
        verus_feedback (Optional[str]): Feedback from Verus verification of the
        buggy proof, if available.
        test_driver_mode (Literal["hardcoded", "stdin"]): The mode of the test
        driver.
    """

    if not raw_program_file.is_file():
        raise FileNotFoundError(f"Raw program file not found: {raw_program_file}")

    test_driver_dir.mkdir(parents=True, exist_ok=True)
    test_driver_file = test_driver_dir / "test_driver.rs"
    # test_driver_gen_response_file = test_driver_dir / "test_driver_gen_response.txt"

    if test_driver_file.is_file() and (test_driver_dir / "output.txt").is_file():
        logger.info(
            f"Skipping test driver generation for {raw_program_file} as it has already been processed."
        )
        return

    extracted_specs = extract_specs_from_proof(gt_proof)
    prompt = compile_test_driver_prompt(
        raw_program_file,
        extracted_specs,
        num_tests=num_tests,
        unverified_or_buggy_proof_file=unverified_or_buggy_proof_file,
        verus_feedback=verus_feedback,
        test_driver_mode=test_driver_mode,
    )

    msg_list = [
        {
            "role": "system",
            "content": VERUS_SYSTEM_PROMPT,
        },
        {"role": "user", "content": prompt},
    ]
    response = request_conversation_one(
        msg_list,
        model=model,
        task_id=str(test_driver_dir),
        prompt_type_id="test_driver_gen",
    )

    write_conversation_file(msg_list, test_driver_dir / "test_gen_conversation.json")

    test_driver_code = extract_rs_code_from_response(response)
    test_driver_file.write_text(test_driver_code)
    test_driver_gen_response_file = test_driver_dir / "test_driver_gen_response.txt"
    test_driver_gen_response_file.write_text(response)

    # Run the test driver
    for i in range(max_retry):
        err_msg = test_driver_run(test_driver_dir, i)
        if err_msg:
            msg_list.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )
            msg_list.append(
                {
                    "role": "user",
                    "content": f"Error compiling or running the test driver: {err_msg}\nPlease fix the test driver and try again.",
                }
            )
            write_conversation_file(
                msg_list, test_driver_dir / "test_gen_conversation.json"
            )
            response = request_conversation_one(
                msg_list,
                model=model,
                temperature=1.0,
                task_id=str(test_driver_dir),
                prompt_type_id="test_driver_fix",
            )
            test_driver_code = extract_rs_code_from_response(response)
            test_driver_file = test_driver_dir / f"test_driver_retry_{i+1}.rs"
            test_driver_file.write_text(test_driver_code)
            test_driver_gen_response_file = (
                test_driver_dir / f"test_driver_gen_response_retry_{i+1}.txt"
            )
            test_driver_gen_response_file.write_text(response)
        else:
            logger.info(
                f"Test driver generated successfully in {test_driver_dir} after {i + 1} attempts."
            )
            return
        if i == max_retry - 1:
            raise RuntimeError(
                f"Failed to generate a valid test driver after {max_retry} attempts for {raw_program_file}."
            )


def test_driver_run(test_driver_dir: Path, i: int) -> str:
    """
    Run the test driver in the specified directory.
    Args:
        test_driver_dir (Path): The directory containing the test driver file.
        i (int): The index of the test driver run
    Returns:
        str: The error message if the test driver fails to run, otherwise an empty string.
    """
    output_file = test_driver_dir / "output.txt"
    if output_file.is_file() and output_file.stat().st_size > 0:
        logger.info(f"Output file already exists and is not empty: {output_file}")
        return ""

    if not test_driver_dir.is_dir():
        raise FileNotFoundError(f"Test driver directory not found: {test_driver_dir}")

    if i == 0:
        test_driver_file = test_driver_dir / "test_driver.rs"
    else:
        test_driver_file = test_driver_dir / f"test_driver_retry_{i}.rs"
    if not test_driver_file.is_file():
        raise FileNotFoundError(f"Test driver file not found: {test_driver_file}")

    # compile the test driver
    compile_cmd = [
        "rustc",
        test_driver_file.as_posix(),
    ]
    compile_result = subprocess.run(
        compile_cmd,
        cwd=test_driver_dir,
        capture_output=True,
    )
    if compile_result.returncode != 0:
        err_msg = compile_result.stderr.decode("utf-8")
        logger.error(f"Compilation failed for {test_driver_file}: {err_msg}")
        return err_msg

    # run the test driver
    run_cmd = [f"./{test_driver_file.stem}"]
    run_result = subprocess.run(
        run_cmd,
        cwd=test_driver_dir,
        capture_output=True,
    )
    if run_result.returncode != 0:
        err_msg = run_result.stderr.decode("utf-8")
        logger.error(f"Test driver failed to run: {err_msg}")
        return err_msg
    else:
        output_file.write_text(run_result.stdout.decode("utf-8"))
        if count_tokens(output_file.read_text()) > OUTPUT_MAX_TOKENS:
            logger.info(
                f"Test output file exceeds maximum token limit ({OUTPUT_MAX_TOKENS}): {output_file}"
            )
            output_file.unlink()  # Remove the output file if it exceeds the limit
            return "[Error] Test output too long, please reduce the size of the test cases."
        logger.info(f"Test driver ran successfully, output written to {output_file}")

    return ""


def main(
    task_type: Literal["ori", "obfs"] = "obfs",
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
    model: str = "gpt-4o",  # both obfuscation and test driver generation
):
    if task_type == "ori":
        proofs = get_all_vb_proofs(
            verified_proof=True,
            use_specified_taskids=False,
            with_invariant=True,
        )
    else:
        proofs = get_all_obfs_proofs(
            prompt_type="plain",
            model=model,
            use_specified_taskids=False,
            with_invariant=True,
        )

    for proof in proofs:
        result_dir = get_result_dir(
            proof,
            prompt_type="plain",
            model=model,
            task_type=task_type,
        )
        test_driver_dir = result_dir / f"test_driver_{model}_{test_driver_mode}"
        print(f"Processing proof {proof.task_id} in {result_dir}...")
        deghosted_unverified_file = list(result_dir.glob("*unverified.rs"))[0]
        deghosted_raw_file = result_dir / "deghosted_raw.rs"

        # check if deghosted_unverified_file is empty
        if (
            not deghosted_unverified_file.is_file()
            or deghosted_unverified_file.stat().st_size == 0
        ):
            raise FileNotFoundError(
                f"Deghosted unverified file not found or is empty in {result_dir}"
            )

        # run llm_instrument with retry
        llm_instrument(
            test_driver_dir,
            deghosted_raw_file,
            proof,
            model=model,
            num_tests=5,
            unverified_or_buggy_proof_file=None,
            verus_feedback=None,  # No feedback for now
            test_driver_mode=test_driver_mode,
            max_retry=5,
        )

    logger.info("Test driver generation completed for all proofs.")


if __name__ == "__main__":
    Fire(main)
