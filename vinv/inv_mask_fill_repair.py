from typing import Literal

from fire import Fire

from vinv.config import INV_GEN_RESULTS_DIR
from vinv.data.cherrypick import get_all_obfs_proofs, get_all_vb_proofs
from vinv.perturb.program.robustness.repair_autoverus_output import repair
from vinv.proof_utils import display_proof_status
from vinv.utils import check_status, get_result_dir, get_test_driver_file
from vinv.verus_utils import verify_with_verus


def main(
    prompt_type: str = "plain",
    model: str = "gpt-4o",
    task_type: Literal["ori", "obfs"] = "ori",
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
    use_test_trace_gen: bool = False,
    use_test_trace_repair: bool = False,
):
    repair_status = {
        "no_need_repair": [],
        "repair_success": [],
        "repair_failed": [],
    }

    if task_type == "obfs":
        proofs = get_all_obfs_proofs(
            prompt_type=prompt_type,
            model=model,
            use_specified_taskids=True,
            with_invariant=True,
        )
    elif task_type == "ori":
        proofs = get_all_vb_proofs(
            verified_proof=True,
            use_specified_taskids=True,
            with_invariant=True,
        )
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    for proof in proofs:
        inv_gen_dir = (
            INV_GEN_RESULTS_DIR / f"{prompt_type}_{model}" / task_type / proof.full_id
        )
        if use_test_trace_gen:
            inv_gen_dir = inv_gen_dir / f"test_trace_gen_{test_driver_mode}"
        else:
            inv_gen_dir = inv_gen_dir / "no_test_trace_gen"

        result_dir = get_result_dir(
            proof,
            task_type=task_type,
            prompt_type=prompt_type,
            model=model,
        )
        test_driver_dir = result_dir / f"test_driver_{model}_{test_driver_mode}"
        test_driver_file = get_test_driver_file(test_driver_dir)
        test_driver_output_file = test_driver_dir / "output.txt"
        assert inv_gen_dir.is_dir(), f"inv_gen directory does not exist: {inv_gen_dir}"

        gen_status_file = inv_gen_dir / "gen_status.txt"

        if not check_status(gen_status_file, "success"):
            continue

        verify_status_file = inv_gen_dir / "verify_status.txt"
        verus_feedback_file = inv_gen_dir / "verus_feedback.txt"
        if check_status(verify_status_file, "verification_pass"):
            repair_status["no_need_repair"].append(proof)
            continue

        incorrected_proof_file = inv_gen_dir / "filled_proof.rs"
        if not verus_feedback_file.exists():
            verify_with_verus(
                incorrected_proof_file,
                stderr_file=verus_feedback_file,
                use_old_verus=False,
                max_errs=5,
            )

        if use_test_trace_repair:
            repair_dir = inv_gen_dir / f"test_trace_repair_{test_driver_mode}"
        else:
            repair_dir = inv_gen_dir / "no_test_trace_repair"
        repair_status_file = repair_dir / "repair_status.txt"
        if repair_status_file.exists():
            repair_success = check_status(repair_status_file, "repair_success")
        else:
            repair_success = repair(
                repair_dir,
                incorrected_proof_file,
                verus_feedback_file,
                test_driver_file,
                test_driver_output_file,
                model,
                use_test_trace=use_test_trace_repair,
                max_retry=10,
            )

        if repair_success:
            repair_status["repair_success"].append(proof)
        else:
            repair_status["repair_failed"].append(proof)

    display_proof_status(repair_status)


if __name__ == "__main__":
    Fire(main)
