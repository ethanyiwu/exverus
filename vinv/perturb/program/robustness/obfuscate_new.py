import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fire import Fire
from loguru import logger

from vinv.config import OBFUSC_RESULTS_DIR
from vinv.data.cherrypick import get_all_vb_proofs
from vinv.gen.client import (
    request_conversation_multi_response,
    request_conversation_one,
)
from vinv.gen.prompt_utils import read_obfuscation_prompt
from vinv.proof import ObfsProofFile
from vinv.utils import check_status, extract_rs_code_from_response
from vinv.verus_utils import get_verus_result, verus_format

REFLECT_MSG = """
The obfuscated program you generated cannot be verified. Please fix it based on the feedback below:
"""

# notes to be highlighted in each round of obfuscation + iterative refinement
OTHER_NOTES = """
* You MUST NOT add any comments in the rust code (otherwise it could leak some hints about obfuscation).
* You MUST NOT use obviously artificial variable/function names containing words like `dummy`, `irrelevant`, `redundant`, (otherwise it could provide hints for the LLM or human that inspects the program).
* You MUST ensure that the invariants in the original program are still preserved in or translated to the obfuscated program and the obfuscated program is still verifiable by Verus. You don't need to add invariants for irrelevant variables unless they are necessary for the verification of the obfuscated program.
* The obfuscated program should maintain naturalness and good readability, i.e., it does not appear to be specifically artificial despite the logic has been significantly complicated.
* The obfuscation MUST NOT make the program unverifiable by Verus, e.g., do not alter the index access pattern (e.g., flipping, skipping, or randomizing indices) which would break the inductive loop reasoning. Instead, preserve sequential access to ensure loop invariants remain valid.
* You MUST have a decrease clause to every loop in the obfuscated program.
* The verus! macro block MUST be at the end of the obfuscated program.
"""


def construct_feedback_message(out: str, err: str) -> str:
    return f"""
stdout:
{out}
stderr:
{err}

### OTHER NOTES
{OTHER_NOTES}
"""


def find_last_obfuscated_file(obfs_gen_dir: Path) -> Optional[Path]:
    """
    Find the last try of obfuscated file in the given directory.
    """
    try:
        # Get all directories that match the pattern "try_*"
        try_dirs = sorted(
            obfs_gen_dir.glob("try_*"), key=lambda x: int(x.name.split("_")[1])
        )
        if not try_dirs:
            return None
        # Get the last directory
        last_try_dir = try_dirs[-1]
        # Find the obfuscated file in the last try directory
        obfuscated_file = last_try_dir / "obfuscated.rs"
        if obfuscated_file.exists():
            return obfuscated_file
        else:
            return None
    except Exception as e:
        logger.error(f"Error finding last obfuscated file: {e}")
        return None


def compile_obfuscate_prompt(
    ori_program: str,
    prompt_type: str = "plain",
) -> str:
    """
    Compile the obfuscation prompt with the original program.
    """
    obfuscate_prompt = read_obfuscation_prompt(prompt_type)
    obfuscate_prompt = obfuscate_prompt.replace("<ori_program>", ori_program).replace(
        "<other_notes>", OTHER_NOTES
    )

    return obfuscate_prompt


def prompt_and_dump_results(
    initial_prompt: str,
    obfs_gen_dir: Path,
    try_cnt: int,
    msg_list: List[Dict],
    model: str = "gpt-4o",
    feedback_msg: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """
    Prompt the LLM to generate an obfuscated program and dump the results.
    """
    obfs_gen_try_cnt_dir = obfs_gen_dir / f"try_{try_cnt}"
    obfs_gen_try_cnt_dir.mkdir(parents=True, exist_ok=True)
    try:
        if try_cnt == 0:
            msg_list.append({"role": "user", "content": initial_prompt})
        else:
            msg_list.append({"role": "user", "content": REFLECT_MSG + feedback_msg})
        gpt_response = request_conversation_one(
            msg_list,
            model=model,
            max_retry=5,
            temperature=1.0,
            task_id=str(obfs_gen_try_cnt_dir),
            prompt_type_id="obfuscate",
            max_tokens=16384,
        )
        obfs_program = extract_rs_code_from_response(gpt_response)

    except Exception as e:
        logger.error(
            f"Error in generating obfuscated program: {e} in directory {obfs_gen_try_cnt_dir}"
        )
        return False, None, None

    msg_list.append({"role": "assistant", "content": gpt_response})

    with open(obfs_gen_try_cnt_dir / "response.txt", "w") as f:
        f.write(gpt_response)

    obfs_file = obfs_gen_try_cnt_dir / "obfuscated.rs"
    with open(obfs_file, "w") as f:
        f.write(obfs_program)

    with open(obfs_gen_try_cnt_dir / "conversations.txt", "w") as f:
        # write formatted conversation
        for msg in msg_list:
            f.write("=" * 20 + "\n")
            f.write(f"{msg['role']}: {msg['content']}\n")

    verified, out, err = get_verus_result(obfs_file, use_old_verus=False)

    return verified, out, err


def prompt_obfuscate_program(ori_program: str, num_responses: int = 5) -> List[str]:
    """
    Obfuscate the original program using the LLM.

    Args:
        ori_program (str): The original Rust program to obfuscate.
        num_responses (int): The number of responses to request from the LLM.

    Returns:
        List[str]: A list of responses containing obfuscated Rust programs.
    """
    prompt = compile_obfuscate_prompt(ori_program)
    responses = request_conversation_multi_response(
        [
            {
                "role": "system",
                "content": "You are an experienced formal language programmer. You are very familiar with Verus, which is a tool for verifying the correctness of code written in Rust.",
            },
            {"role": "user", "content": prompt},
        ],
        num_responses=num_responses,
        task_id="obfuscate_ad_hoc",
        prompt_type_id="obfuscate_multi",
    )

    return responses


def process_proof(proof, prompt_type, model, num_responses, max_try):
    work_dir = OBFUSC_RESULTS_DIR / f"{prompt_type}_{model}" / proof.task_id
    work_dir.mkdir(parents=True, exist_ok=True)
    gt_proof_file = work_dir / "gt_proof.rs"
    shutil.copy(proof.path, gt_proof_file)
    initial_prompt = compile_obfuscate_prompt(
        gt_proof_file.read_text(),
        prompt_type,
    )
    # 跳过整个 proof（只要有一个 response 已经 verified）
    for i in range(num_responses):
        status_file = work_dir / f"response_{i}" / "OBFS_GEN_STATUS.txt"
        if status_file.exists():
            try:
                if "OBFS_VERUS_VERIFIED" in status_file.read_text():
                    logger.info(f"Skipping proof {proof.task_id} as it is already verified in response {i}.")
                    return
            except Exception as e:
                logger.warning(f"Error reading status file: {e}")
                continue
    for i in range(num_responses):
        response_dir = work_dir / f"response_{i}"
        status_file = response_dir / "OBFS_GEN_STATUS.txt"
        feedback_msg = None
        out, err = "", ""
        conversation = [
            {
                "role": "system",
                "content": "You are an experienced formal language programmer. You are very familiar with Verus, which is a tool for verifying the correctness of code written in Rust.",
            }
        ]
        for k in range(max_try):
            try_dir = response_dir / f"try_{k}"
            try_dir.mkdir(parents=True, exist_ok=True)
            if k > 0:
                feedback_msg = construct_feedback_message(out, err)
            verified, out, err = prompt_and_dump_results(
                initial_prompt,
                response_dir,
                k,
                conversation,
                model,
                feedback_msg,
            )
            if verified:
                status_file.write_text("OBFS_VERUS_VERIFIED")
                obfuscated_file = find_last_obfuscated_file(response_dir)
                formatted_obfuscated_file = response_dir / "obfuscated_formatted.rs"
                shutil.copy(obfuscated_file, formatted_obfuscated_file)
                if not verus_format(formatted_obfuscated_file):
                    logger.info(
                        f"Failed to format obfuscated program {i} for proof {proof.task_id}."
                    )
                else:
                    logger.info(
                        f"Obfuscated program {i} for proof {proof.task_id} saved and formatted successfully."
                    )
                    # deghost the formatted obfuscated program
                    if check_status(status_file, "OBFS_VERUS_VERIFIED"):
                        formatted_obfuscated_file = (
                            response_dir / "obfuscated_formatted.rs"
                        )
                        obfs_proof = ObfsProofFile(formatted_obfuscated_file, proof)
                        deghosted_raw_file = response_dir / "deghosted_raw.rs"
                        deghosted_unverified_file = (
                            response_dir / "deghosted_unverified.rs"
                        )
                        deghosted_raw_file.write_text(
                            obfs_proof.deghostify(deghost_mode="raw", run_fmt=True)
                        )
                        deghosted_unverified_file.write_text(
                            obfs_proof.deghostify(
                                deghost_mode="unverified", run_fmt=True
                            )
                        )
                break
            else:
                if k == max_try - 1:
                    status_file.write_text("OBFS_VERUS_FAILED")
                    logger.warning(
                        f"Failed to verify obfuscated program (response {i}) for proof {proof.task_id} after {max_try} tries."
                    )


def main(
    verusage: bool = False,
    sample: bool = False,
    prompt_type: str = "plain",
    num_responses: int = 5,
    max_try: int = 10,
    model: str = "gpt-4o",
):
    
    if verusage:
        proofs = get_all_vb_proofs(
            verified_proof=True,
            use_specified_taskids=True,
            with_invariant=False,
            source="VERUSAGE",
        )
    else:
        proofs = get_all_vb_proofs(
            verified_proof=True,
            use_specified_taskids=True,
            with_invariant=True,
        )
    
    if sample:
        # sample 5 proofs for testing
        import random 
        random.seed(42)
        proofs = random.sample(proofs, 5)
    
    # import pdb; pdb.set_trace()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_proof, proof, prompt_type, model, num_responses, max_try) for proof in proofs]
        for f in futures:
            f.result()


if __name__ == "__main__":
    Fire(main)
