import shutil

from fire import Fire
from loguru import logger

from vinv.data.cherrypick import get_all_obfs_proofs
from vinv.gen.inv_gen import mask_and_fill_invariant
from vinv.proof_utils import display_proof_status
from vinv.utils import diff
from vinv.verus_utils import record_verify_status, verify_with_verus


def main(
    obfuscate_prompt_type: str = "plain",
    mask_fill_prompt_type: str = "plain",
    model: str = "gpt-4o",
):
    obfs_proofs = get_all_obfs_proofs(
        prompt_type=obfuscate_prompt_type,
        model=model,
        use_specified_taskids=True,
        with_invariant=True,
    )

    proof_status = {
        "compilation_error": [],
        "verification_error": [],
        "verification_pass": [],
    }

    for obfs_proof in obfs_proofs:
        response_dir = obfs_proof.path.parent
        mask_fill_dir = response_dir / f"mask_fill_{mask_fill_prompt_type}"
        gen_status_file = (
            mask_fill_dir / "gen_status.txt"
        )  # gen_status.txt is used to track the mask-fill generation status
        filled_proof_file = mask_fill_dir / "filled_proof.rs"
        if gen_status_file.is_file():
            logger.warning(f"Skipping {response_dir} as it has already been processed.")
        else:
            filled_proof_file = mask_and_fill_invariant(
                obfs_proof,
                prompt_type=mask_fill_prompt_type,
                work_dir=mask_fill_dir,
                mask_all=True,
                model=model,
            )

        if filled_proof_file is None:
            logger.warning(
                f"Skipping verification for {obfs_proof.path} due to generation status: {gen_status_file.read_text().strip()}"
            )
            continue

        verify_status_file = mask_fill_dir / "verify_status.txt"
        gt_proof_file = mask_fill_dir / "gt_proof.rs"
        shutil.copy(obfs_proof.path, gt_proof_file)
        if verify_status_file.is_file():
            logger.info(f"Skipping {mask_fill_dir} as it has already been processed.")
        else:
            verus_out_file = mask_fill_dir / "verus_out.txt"
            verus_err_file = mask_fill_dir / "verus_err.txt"
            verify_with_verus(
                filled_proof_file,
                stdout_file=verus_out_file,
                stderr_file=verus_err_file,
            )

            # run verus on the proof with the filled invariants
            record_verify_status(
                filled_proof_file,
                verify_status_file,
            )

            invariant_diff = mask_fill_dir / "filled_vs_gt.diff"
            diff(
                filled_proof_file,
                gt_proof_file,
                invariant_diff,
            )

        status = verify_status_file.read_text().strip()
        proof_status[status].append(obfs_proof)

    # Print the results
    display_proof_status(proof_status)


if __name__ == "__main__":
    Fire(main)
