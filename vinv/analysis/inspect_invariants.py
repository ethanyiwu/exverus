from fire import Fire

from vinv.config import INV_GEN_RESULTS_DIR
from vinv.data.cherrypick import get_all_vb_proofs


def main(
    prompt_type: str = "plain",
    model: str = "gpt-4o",
):
    proofs = get_all_vb_proofs(with_invariant=True)

    for proof in proofs:
        work_dir = INV_GEN_RESULTS_DIR / f"{prompt_type}_{model}" / proof.task_id
        work_dir.mkdir(parents=True, exist_ok=True)

        invariant_diff = work_dir / "filled_vs_gt.diff"
        gen_status_file = work_dir / "gen_status.txt"
        if gen_status_file.read_text().strip() != "success":
            continue

        verify_status = (work_dir / "verify_status.txt").read_text().strip()
        if verify_status == "verification_pass":
            print(f"verification pass: {invariant_diff}")
        elif verify_status == "verification_error":
            print(f"verification error: {invariant_diff}")
        else:
            print(f"compilation error: {invariant_diff}")


if __name__ == "__main__":
    Fire(main)
