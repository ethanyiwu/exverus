from typing import Dict, List, Literal, Tuple

from fire import Fire

from vinv.data.cherrypick import get_all_vb_proofs
from vinv.invariant import parse_invariant_items
from vinv.proof import ProofFile


def classify_by_thresholds(x: int, a: int, b: int) -> Literal["low", "mid", "high"]:
    if x < a:
        return "low"
    if x < b:
        return "mid"
    return "high"


def count_num_invariants(proof: ProofFile) -> int:
    invariant_entry_map = proof.parse_invariants()
    num_invariants = 0
    for func_id in invariant_entry_map:
        invariant_entry_list = invariant_entry_map[func_id]
        for invariant_entry in invariant_entry_list:
            invariant_items = parse_invariant_items(invariant_entry)
            num_invariants += len(invariant_items)

    return num_invariants


def count_num_assertions(proof: ProofFile) -> int:
    return proof.code.count("assert(")


def count_num_spec_func(proof: ProofFile) -> int:
    return proof.code.count("spec fn")


def count_num_proof(proof: ProofFile) -> int:
    return proof.code.count("proof fn") + proof.code.count("proof {")


def main(
    source: Literal["CLEANED_VB", "ADDITIONAL", "THREEBENCH", "VSBHERB"] = "CLEANED_VB",
):
    all_verified_proofs = get_all_vb_proofs(
        verified_proof=True,
        use_specified_taskids=False,
        with_invariant=False,
        remove_blacklisted=True,
        source=source,
    )

    # Collect metrics per proof
    per_proof_rows: List[Dict[str, int | str]] = []
    invariants_counts: List[int] = []
    assertions_counts: List[int] = []
    proof_fn_counts: List[int] = []

    for proof in all_verified_proofs:
        num_invariants = count_num_invariants(proof)
        num_assertions = count_num_assertions(proof)
        num_proof = count_num_proof(proof)

        invariants_counts.append(num_invariants)
        assertions_counts.append(num_assertions)
        proof_fn_counts.append(num_proof)

        per_proof_rows.append(
            {
                "task_id": proof.full_id,
                "invariants": num_invariants,
                "assertions": num_assertions,
                "proof_fns": num_proof,
            }
        )

    a_inv, b_inv = 5, 100
    a_asr, b_asr = 1, 100
    a_prf, b_prf = 1, 100

    # Compute distribution for each metric
    def dist(values: List[int], a: int, b: int) -> Tuple[int, int, int]:
        low = sum(1 for v in values if v < a)
        mid = sum(1 for v in values if a <= v < b)
        high = sum(1 for v in values if v >= b)
        return low, mid, high

    inv_dist = dist(invariants_counts, a_inv, b_inv)
    asr_dist = dist(assertions_counts, a_asr, b_asr)
    prf_dist = dist(proof_fn_counts, a_prf, b_prf)

    print("=" * 80)
    print(f"Source: {source}")
    print(f"Num proofs: {len(all_verified_proofs)}")
    print(
        "- Invariants thresholds: a =",
        a_inv,
        ", b =",
        b_inv,
        " => counts (low, mid, high)=",
        inv_dist,
    )
    print(
        "- Assertions thresholds: a =",
        a_asr,
        ", b =",
        b_asr,
        " => counts (low, mid, high)=",
        asr_dist,
    )
    print(
        "- Proof fns thresholds: a =",
        a_prf,
        ", b =",
        b_prf,
        " => counts (low, mid, high)=",
        prf_dist,
    )

    # Optional: show per-task classification summary (compact)
    for row in per_proof_rows:
        inv_grp = classify_by_thresholds(int(row["invariants"]), a_inv, b_inv)
        asr_grp = classify_by_thresholds(int(row["assertions"]), a_asr, b_asr)
        prf_grp = classify_by_thresholds(int(row["proof_fns"]), a_prf, b_prf)
        print(
            f"{row['task_id']}: inv={row['invariants']}({inv_grp}), asr={row['assertions']}({asr_grp}), proof={row['proof_fns']}({prf_grp})"
        )


if __name__ == "__main__":
    Fire(main)
