from pathlib import Path

from vinv.config import ORI_BENCHMARK_ROOT_DIR
from vinv.proof import ObfsProofFile, ProofFile


def test_parse_invariants():
    # Test parsing invariants from a proof file
    ori_proof_file = ProofFile(
        ORI_BENCHMARK_ROOT_DIR / "CloverBench/verified/linear_search2.rs"
    )
    obfs_proof_file = ObfsProofFile(
        Path("tests/data/cloverbench_linear_search2_obfs.rs"), ori_proof_file
    )
    invariants = obfs_proof_file.parse_invariants()
    assert len(invariants) == 1, "Expected 1 invariant"
    invariant_entry = invariants["linear_search2_7_39"][0]
    assert len(invariant_entry.invariants_code.splitlines()) == 4
