from pathlib import Path
from typing import Literal

from fire import Fire
from loguru import logger

from vinv.config import ROOT_DIR
from vinv.data.cherrypick import get_all_obfs_proofs
from vinv.gen.client import request_conversation_one
from vinv.gen.prompt_utils import (
    TEST_TRACE_INFO_PROMPT,
    VERUS_SYSTEM_PROMPT,
    read_repair_with_trace_prompt,
    write_conversation_file,
)
from vinv.lynette_utils import code_change_is_safe
from vinv.proof_utils import display_proof_status
from vinv.utils import check_status, extract_rs_code_from_response, program_with_line_no
from vinv.verus_utils import get_verus_result, verify_with_verus

AUTOVERUS_TOOL_DIR = ROOT_DIR / "verus-proof-synthesis" / "code"


def repair(
    repair_dir: Path,
    incorrect_proof_file: Path,
    verus_feedback_file: Path,
    test_driver_file: Path,
    test_driver_output_file: Path,
    model: str = "gpt-4o",
    use_test_trace: bool = True,
    max_retry: int = 3,
) -> bool:
    repair_dir.mkdir(parents=True, exist_ok=True)
    prompt = compile_repair_with_trace_prompt(
        incorrect_proof_file,
        verus_feedback_file,
        test_driver_file,
        test_driver_output_file,
        use_test_trace=use_test_trace,
    )
    msg_list = [
        {
            "role": "system",
            "content": VERUS_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    response = request_conversation_one(
        msg_list,
        model=model,
        temperature=1.0,
        task_id=str(repair_dir),
        prompt_type_id="trace_repair",
    )

    write_conversation_file(msg_list, repair_dir / "trace_repair_conversation.json")

    repaired_proof_code = extract_rs_code_from_response(response)
    repaired_proof_file = repair_dir / "repaired_proof.rs"
    response_file = repair_dir / "response.txt"
    response_file.write_text(response)
    repair_status_file = repair_dir / "repair_status.txt"
    repaired_proof_file.write_text(repaired_proof_code)

    # Verify the repaired proof
    for i in range(max_retry):
        success, stdout, stderr = get_verus_result(repaired_proof_file)
        is_safe_code_change = code_change_is_safe(
            incorrect_proof_file, repaired_proof_file
        )
        if success and is_safe_code_change:
            repair_status_file.write_text("repair_success")
            logger.info(f"Repair succeeded for {repair_dir} on attempt {i + 1}.")
            return True
        else:
            msg_list.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )
            if success:
                stderr = "The new proof broke the original execution code, you MUST NOT change the execution code!"
            if not success and not is_safe_code_change:
                stderr += "The new proof broke the original execution code, you MUST NOT change the execution code!"
            msg_list.append(
                {
                    "role": "user",
                    "content": f"Repair failed with error: {stderr}\n Please fix the proof and try again.",
                }
            )
            write_conversation_file(
                msg_list, repair_dir / "trace_repair_conversation.json"
            )
            response = request_conversation_one(
                msg_list,
                model=model,
                temperature=1.0,
                task_id=str(repair_dir),
                prompt_type_id="trace_repair_retry",
            )
            repaired_proof_code = extract_rs_code_from_response(response)
            repaired_proof_file = repair_dir / f"repaired_proof_retry_{i + 1}.rs"
            repaired_proof_file.write_text(repaired_proof_code)
            response_file = repair_dir / f"response_retry_{i + 1}.txt"
            response_file.write_text(response)

    repair_status_file.write_text("repair_failed")
    logger.warning(f"Repair failed for {repair_dir} after {max_retry} attempts.")
    return False


def compile_repair_with_trace_prompt(
    incorrect_proof_file: Path,
    verus_feedback_file: Path,
    test_driver_file: Path,
    test_driver_output_file: Path,
    use_test_trace: bool = True,
) -> str:
    """
    Compile the repair with trace prompt.
    Args:
        incorrect_proof_file (Path): The path to the incorrect proof file.
        verus_feedback_file (Path): The path to the Verus feedback file.
        test_driver_file (Path): The path to the test driver file.
        test_driver_output_file (Path): The path to the test driver output file.
        use_test_trace (bool): Whether to use test trace in the prompt.
    Returns:
        str: The output of the compilation command.
    """
    prompt = read_repair_with_trace_prompt()
    if use_test_trace:
        prompt = prompt.replace("<test_trace_info>", TEST_TRACE_INFO_PROMPT)
    else:
        prompt = prompt.replace("<test_trace_info>", "")

    prompt = (
        prompt.replace("<incorrect_proof>", incorrect_proof_file.read_text())
        .replace("<verus_feedback>", verus_feedback_file.read_text())
        .replace("<test_driver_code>", program_with_line_no(test_driver_file))
        .replace("<execution_output>", test_driver_output_file.read_text())
    )

    return prompt


def main(
    obfuscate_prompt_type: str = "plain",
    model: str = "gpt-4o",
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
    use_test_trace: bool = False,
):
    repair_status = {
        "repair_success": [],
        "repair_failed": [],
    }
    obfs_proofs = get_all_obfs_proofs(
        prompt_type=obfuscate_prompt_type,
        model=model,
        use_specified_taskids=True,
        with_invariant=True,
    )

    for obfs_proof in obfs_proofs:
        response_dir = obfs_proof.path.parent
        deghosted_unverified_file = response_dir / "deghosted_unverified.rs"

        # check if deghosted_unverified_file is empty
        if (
            not deghosted_unverified_file.is_file()
            or deghosted_unverified_file.stat().st_size == 0
        ):
            raise FileNotFoundError(
                f"Deghosted unverified file not found or is empty in {response_dir}"
            )

        # check autoverus results
        autoverus_result_dir = response_dir / "autoverus_result"
        autoverus_output_file = autoverus_result_dir / "autoverus_output.rs"
        autoverus_status_file = autoverus_result_dir / "autoverus_status.txt"
        # stderr_file = autoverus_result_dir / "autoverus_stderr.txt"
        verus_feedback_file = autoverus_result_dir / "verus_feedback.txt"

        if check_status(autoverus_status_file, "verification_pass"):
            continue

        if not verus_feedback_file.exists():
            verify_with_verus(
                autoverus_output_file,
                stderr_file=verus_feedback_file,
                use_old_verus=False,
                max_errs=5,
            )

        # repair the autoverus output with trace
        if use_test_trace:
            repair_dir = autoverus_result_dir / f"repair_trace_{test_driver_mode}"
        else:
            repair_dir = autoverus_result_dir / "repair_no_trace"
        test_driver_file = (
            response_dir / f"test_driver_{model}_{test_driver_mode}" / "test_driver.rs"
        )
        test_driver_output_file = (
            response_dir / f"test_driver_{model}_{test_driver_mode}" / "output.txt"
        )
        repair_status_file = repair_dir / "repair_status.txt"
        if repair_status_file.exists():
            repair_success = check_status(repair_status_file, "repair_success")
        else:
            repair_success = repair(
                repair_dir,
                autoverus_output_file,
                verus_feedback_file,
                test_driver_file,
                test_driver_output_file,
                model=model,
                use_test_trace=use_test_trace,
            )

        if repair_success:
            repair_status["repair_success"].append(obfs_proof)
        else:
            repair_status["repair_failed"].append(obfs_proof)

    # Print the results
    display_proof_status(repair_status)


if __name__ == "__main__":
    Fire(main)
