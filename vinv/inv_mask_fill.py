import shutil
import subprocess
from typing import Literal

from fire import Fire
from loguru import logger

from vinv.config import INV_GEN_RESULTS_DIR
from vinv.data.cherrypick import get_all_obfs_proofs, get_all_vb_proofs
from vinv.gen.inv_gen import mask_and_fill_invariant
from vinv.proof_utils import display_proof_status
from vinv.utils import check_status, get_result_dir, get_test_driver_file
from vinv.verus_utils import record_verify_status


def main(
    prompt_type: str = "plain",
    model: str = "gpt-4o",
    task_type: Literal["ori", "obfs"] = "ori",
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
    use_test_trace: bool = False,
):
    proof_status = {
        "compilation_error": [],
        "verification_error": [],
        "verification_pass": [],
    }

    if task_type == "obfs":
        proofs = get_all_obfs_proofs(
            prompt_type=prompt_type,
            model=model,
            use_specified_taskids=False,
            with_invariant=True,
        )
    elif task_type == "ori":
        proofs = get_all_vb_proofs(
            verified_proof=True,
            use_specified_taskids=False,
            with_invariant=True,
        )
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    for proof in proofs:
        work_dir = (
            INV_GEN_RESULTS_DIR / f"{prompt_type}_{model}" / task_type / proof.full_id
        )
        if use_test_trace:
            work_dir = work_dir / f"test_trace_gen_{test_driver_mode}"
        else:
            work_dir = work_dir / "no_test_trace_gen"
        result_dir = get_result_dir(
            proof,
            task_type=task_type,
            prompt_type=prompt_type,
            model=model,
        )
        test_driver_dir = result_dir / f"test_driver_{model}_{test_driver_mode}"
        test_driver_file = get_test_driver_file(test_driver_dir)
        test_driver_output_file = test_driver_dir / "output.txt"
        work_dir.mkdir(parents=True, exist_ok=True)
        gt_proof_file = work_dir / "gt_proof.rs"
        shutil.copy(proof.path, gt_proof_file)
        filled_proof_file = work_dir / "filled_proof.rs"
        gen_status_file = work_dir / "gen_status.txt"
        if gen_status_file.exists():
            logger.info(f"Skipping {proof.path} as it has already been processed.")
        else:
            mask_and_fill_invariant(
                proof,
                prompt_type,
                work_dir,
                mask_all=True,
                model=model,
                use_test_trace=use_test_trace,
                test_driver_file=test_driver_file,
                test_driver_output_file=test_driver_output_file,
            )

        if not check_status(gen_status_file, "success"):
            logger.warning(
                f"Skipping verification for {proof.path} due to generation status: {gen_status_file.read_text().strip()}"
            )
            continue

        verify_status_file = work_dir / "verify_status.txt"
        if not verify_status_file.exists():
            record_verify_status(
                filled_proof_file,
                verify_status_file,
            )

            invariant_diff = work_dir / "filled_vs_gt.diff"
            cmd = [
                "diff",
                "-uw",
                filled_proof_file.as_posix(),
                gt_proof_file.as_posix(),
            ]
            subprocess.run(
                cmd, stdout=invariant_diff.open("w"), stderr=subprocess.DEVNULL
            )
        else:
            logger.info(
                f"Skipping verification for {proof.path} as it has already been processed."
            )

        proof_status[verify_status_file.read_text().strip()].append(proof)

    # Print the results
    display_proof_status(proof_status)


if __name__ == "__main__":
    Fire(main)
