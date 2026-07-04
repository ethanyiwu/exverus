import json
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from loguru import logger

from vinv.gen.client import request_conversation_one
from vinv.gen.prompt_utils import (
    make_unified_diff,
    read_compilation_repair_prompt,
    read_naive_repair_prompt,
)
from vinv.proof import ProofFile
from vinv.utils import check_status, extract_rs_code_from_response
from vinv.verus_utils import record_verify_status, verify_with_verus

NAIVE_REFLECT_MSG = """
The proof file you generated is not correct. The verification failed. Please reflect and try again.
Error message:
"""

COMPILATION_REFLECT_MSG = """
The proof file you generated still has compilation errors. Please focus only on fixing the compilation errors.
Error message:
"""


def prompt_and_dump_results(
    initial_prompt: str,
    repair_dir: Path,
    try_cnt: int,
    msg_list: List[Dict],
    model: str,
    feedback_msg: str,
    repair_strategy: Literal["naive", "compilation"] = "naive",
    before_repair_file: Path = None,
) -> bool:
    """
    Prompt the LLM to repair the code and dump the results.
    Args:
        initial_prompt (str): The initial prompt to start the conversation.
        repair_dir (Path): The directory to store the repair results.
        try_cnt (int): The current attempt number.
        msg_list (List[Dict]): The list of messages in the conversation.
        feedback_msg (str): The feedback message to include in the prompt.
        repair_strategy (str): The repair strategy to use ("naive" or "compilation").
        before_repair_file (Path): The file before repair.
    """
    repair_try_cnt_dir = repair_dir / f"try_{try_cnt}"
    repair_try_cnt_dir.mkdir(parents=True, exist_ok=True)
    if try_cnt == 1:
        assert len(msg_list) == 1, "Initial prompt should only have one message."
        msg_list.append(
            {
                "role": "user",
                "content": initial_prompt,
            }
        )
    else:
        msg_list.append(
            {
                "role": "user",
                "content": (
                    NAIVE_REFLECT_MSG
                    if repair_strategy == "naive"
                    else COMPILATION_REFLECT_MSG
                )
                + feedback_msg,
            }
        )
    try:
        response = request_conversation_one(
            msg_list,
            model=model,
            max_retry=5,
            temperature=1.0,
            task_id=str(repair_try_cnt_dir),
            prompt_type_id=(
                "naive_repair" if repair_strategy == "naive" else "compilation_repair"
            ),
        )
        msg_list.append({"role": "assistant", "content": response})
    except Exception as e:
        logger.error(f"Failed to get response from API: {str(e)}")
        return False

    # Retry logic for extracting Rust code from response
    max_extract_retry = 3
    for attempt in range(1, max_extract_retry + 1):
        try:
            repaired_code = extract_rs_code_from_response(response)
            if repaired_code.strip():
                break
            logger.warning(
                f"Failed to extract Rust code from response (attempt {attempt}). Retrying conversation..."
            )
            # Optionally, you can modify the prompt or message list here to ask for correct format
            response = request_conversation_one(
                msg_list,
                model=model,
                max_retry=5,
                temperature=1.0,
                task_id=str(repair_try_cnt_dir),
                prompt_type_id=(
                    "naive_repair_retry"
                    if repair_strategy == "naive"
                    else "compilation_repair_retry"
                ),
            )
            msg_list[-1]["content"] = response
        except ValueError as e:
            logger.error(f"Failed to extract code: {str(e)}")
            if attempt == max_extract_retry:
                msg_list[-1]["content"] = response
                return False
            continue
        except Exception as e:
            logger.error(f"Unexpected error while extracting code: {str(e)}")
            msg_list[-1]["content"] = response
            return False
    else:
        logger.error(
            "Failed to extract Rust code from response after multiple attempts."
        )
        repaired_code = ""

    # Only write files if we have valid content
    assert (
        repaired_code and response
    ), f"Repaired code or response is empty for {repair_try_cnt_dir}"
    with open(repair_try_cnt_dir / "repaired.rs", "w") as f:
        f.write(repaired_code)
    with open(repair_try_cnt_dir / "response.txt", "w") as f:
        f.write(response)
    with open(repair_try_cnt_dir / "conversation.json", "w") as f:
        f.write(json.dumps(msg_list, indent=4))

    before_text = before_repair_file.read_text()
    make_unified_diff(
        before_text,
        repaired_code,
        out_path=repair_try_cnt_dir / "diff_before_after.diff",
    )

    return True


def compile_naive_repair_prompt(
    proof_file: ProofFile,
    console_error_message: str,
    original_proof_file: Path | None = None,
) -> str:
    """
    Compile the naive repair prompt. Optionally accept the original unverified proof
    and inject a unified diff highlighting the delta between original and buggy proofs.
    """
    prompt_template = read_naive_repair_prompt()
    buggy = proof_file.path.read_text()
    original = (
        original_proof_file.read_text() if original_proof_file is not None else ""
    )
    diff_text = make_unified_diff(original, buggy)

    prompt = (
        prompt_template.replace("<buggy_proof>", buggy)
        .replace("<original_proof>", original)
        .replace("<diff>", diff_text)
        .replace("<console_error_message>", console_error_message)
        .replace("<error_message>", console_error_message)
    )

    return prompt


def compile_compilation_repair_prompt(
    proof_file: ProofFile,
    console_error_message: str,
    original_proof_file: Path | None = None,
) -> str:
    """
    Compile the compilation repair prompt that focuses on fixing compilation errors.
    Optionally accept the original unverified proof and inject a unified diff.
    """
    prompt_template = read_compilation_repair_prompt()
    buggy = proof_file.path.read_text()
    original = (
        original_proof_file.read_text() if original_proof_file is not None else ""
    )
    diff_text = make_unified_diff(original, buggy)

    prompt = (
        prompt_template.replace("{proof_content}", buggy)
        .replace("{original_proof}", original)
        .replace("{diff}", diff_text)
        .replace("{error_message}", console_error_message)
    )

    return prompt


def iterative_repair(
    error_proof_file: ProofFile,
    console_error_message: str,
    repair_dir: Path,
    model: str = "gpt-4o",
    max_try: int = 5,
    repair_strategy: Literal["naive", "compilation"] = "naive",
    original_proof_file: Path | None = None,
) -> Tuple[Path, bool]:
    """
    Prompt an LLM to iteratively repair the proof file based on the console error message.
    For naive repair, the goal is to get to the verification pass.
    For compilation repair, the goal is to get to either the verification pass or the verification error.
    Args:
        error_proof_file: The proof file to repair
        console_error_message: The error message from the console
        repair_dir: Directory to store repair attempts
        model: The LLM model to use
        max_try: Maximum number of repair attempts
        repair_strategy: Strategy to use for repair ("naive" or "compilation")
    """
    if repair_strategy == "naive":
        initial_prompt = compile_naive_repair_prompt(
            error_proof_file,
            console_error_message,
            original_proof_file=original_proof_file,
        )
    elif repair_strategy == "compilation":
        initial_prompt = compile_compilation_repair_prompt(
            error_proof_file,
            console_error_message,
            original_proof_file=original_proof_file,
        )
    else:
        raise ValueError(f"Unknown repair strategy: {repair_strategy}")
    msg_list = [
        {
            "role": "system",
            "content": "You are an experienced formal language programmer. You are very familiar with Verus, which is a tool for verifying the correctness of code written in Rust.",
        }
    ]
    repaired_code_path = None
    for repair_attempt in range(1, max_try + 1):
        success = prompt_and_dump_results(
            initial_prompt=initial_prompt,
            repair_dir=repair_dir,
            try_cnt=repair_attempt,
            msg_list=msg_list,
            model=model,
            feedback_msg=console_error_message,
            repair_strategy=repair_strategy,
            before_repair_file=original_proof_file
            if repair_attempt == 1
            else repaired_code_path,
        )

        if not success:
            logger.error(f"Failed to get valid response on attempt {repair_attempt}")
            continue

        # Check if the repaired code passes the verification
        repaired_code_path = repair_dir / f"try_{repair_attempt}" / "repaired.rs"
        if repaired_code_path.is_file():
            stdout_file = repair_dir / f"try_{repair_attempt}" / "out.txt"
            stderr_file = repair_dir / f"try_{repair_attempt}" / "err.txt"
            repair_status_file = repair_dir / f"{repair_strategy}_repair_status.txt"

            verification_passed = verify_with_verus(
                proof_file=repaired_code_path,
                stdout_file=stdout_file,
                stderr_file=stderr_file,
            )
            verification_passed_2 = record_verify_status(
                repaired_code_path,
                repair_status_file,
                override=True,
            )
            assert (
                verification_passed == verification_passed_2
            ), f"Verification status mismatch for {repaired_code_path}"
            if verification_passed:
                logger.info(
                    f"Verification passed for {repaired_code_path} on attempt {repair_attempt}."
                )
                return repaired_code_path, True
            else:
                console_error_message = (
                    f"{stderr_file.read_text()}\n{stdout_file.read_text()}"
                )
                if repair_strategy == "compilation" and check_status(
                    repair_status_file, "verification_error"
                ):
                    logger.info(
                        f"Compilation repair reached verification error for {repaired_code_path} on attempt {repair_attempt}."
                    )
                    return repaired_code_path, False
        else:
            raise FileNotFoundError(
                f"Repaired code file not found: {repaired_code_path}"
            )

    return repaired_code_path, False
