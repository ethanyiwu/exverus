import difflib
import json
from pathlib import Path
from typing import List

from vinv.config import (
    AUTOVERUS_TRAJECTORY_RESULTS_DIR,
    TRAJECTORY_RESULT_FILE,
    VB_VERIFY_FAILED_BLACKLIST,
)
from vinv.data.cherrypick import get_all_vb_proofs
from vinv.proof import ProofFile


def get_diff_content(file_path: Path, gt_proof: ProofFile):
    file_code = file_path.read_text()
    gt_code = gt_proof.code
    diff = difflib.unified_diff(
        file_code.splitlines(), gt_code.splitlines(), lineterm=""
    )
    return "\n".join(diff)


def parse_trajectory_result(
    all_verified_proofs: List[ProofFile],
):
    with open(TRAJECTORY_RESULT_FILE, "r") as f:
        trajectory_dict = json.load(f)

    for task_full_id, file_dict_list in trajectory_dict.items():
        task_name = task_full_id.split("-")[-1]
        benchmark = task_full_id.split("-")[2].replace("clover", "cloverbench")
        task_id = f"{benchmark}_{task_name}"
        if task_id in VB_VERIFY_FAILED_BLACKLIST:
            continue
        print(f"Processing task {task_id}")
        gt_proof = [p for p in all_verified_proofs if p.task_id == task_id][0]
        assert (
            gt_proof.task_id == task_id
        ), f"Task ID mismatch: {gt_proof.task_id} != {task_id}"
        for file_dict in file_dict_list:
            file_path_str = file_dict["path"]
            file_path = AUTOVERUS_TRAJECTORY_RESULTS_DIR / file_path_str
            assert file_path.is_file(), f"File not found: {file_path}"

            diff_content = get_diff_content(file_path, gt_proof)
            print(file_path)
            print(gt_proof.path)
            print(diff_content)


if __name__ == "__main__":
    all_verified_proofs = get_all_vb_proofs(
        verified_proof=True, use_specified_taskids=False
    )
    parse_trajectory_result(all_verified_proofs)
