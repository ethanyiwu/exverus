from pathlib import Path
from typing import Dict, List

from vinv.config import (
    CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS,
    OBFUSC_RESULTS_DIR,
    ORI_RESULTS_DIR,
)
from vinv.proof import ProofFile


def display_proof_status(proof_status: Dict[str, List[ProofFile]]) -> None:
    """
    Display the status of proofs in a readable format.
    Args:
        proof_status (Dict[str, List[ProofFile]]): A dictionary containing proof statuses.
    """
    for status, proofs in proof_status.items():
        print(f"{status}: {len(proofs)} proofs")
        for proof in proofs:
            print(f"  - {proof.full_id}")


def get_result_dir(
    proof: ProofFile,
    task_type: str,
    prompt_type: str = "plain",
    model: str = "gpt-4o",
) -> Path:
    if task_type == "ori":
        result_dir = ORI_RESULTS_DIR / proof.full_id
    elif task_type == "obfs":
        result_dir = (
            OBFUSC_RESULTS_DIR
            / f"{prompt_type}_{model}"
            / proof.task_id
            / proof.obfs_id
        )
    elif task_type == "autoverus":
        result_dir = proof.path.parent
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    return result_dir


def get_proof_by_id(proof_id: str, verified: bool = True) -> ProofFile:
    """
    Get a proof file by its ID.
    Args:
        proof_id (str): The ID of the proof, e.g., "verusbench_mbpp_task_id_436"
        verified (bool): Whether the proof is verified.
    Returns:
        ProofFile: The proof file.
    """
    assert proof_id.startswith("verusbench"), "only verusbench proofs are supported"
    benchmark_id = proof_id.split("_")[1]
    task_id = "_".join(proof_id.split("_")[2:])
    if verified:
        proof_file_path = (
            CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS[benchmark_id] / f"{task_id}.rs"
        )
    else:
        proof_file_path = (
            CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS[benchmark_id] / f"{task_id}.rs"
        )

    return ProofFile(proof_file_path)


def extract_proof_id_from_path(proof_path: Path, benchmark_id: str) -> str:
    """
    Extract the proof ID from the path.
    Args:
        proof_path (Path): The path to the proof file.
        benchmark_id (str): The ID of the benchmark, lower case.
    Returns:
        str: The proof ID.
    """
    for element in proof_path.parts:
        if element.startswith(benchmark_id):
            return element

    raise ValueError(
        f"Benchmark ID {benchmark_id} not found in proof path {proof_path}"
    )
