import random
import shutil
from typing import List, Literal

from fire import Fire
from loguru import logger
from lynette import lynette

from vinv.config import (
    ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS,
    AUTOVERUS_ALMOST_CORRECT_RESULTS_DIR,
    AUTOVERUS_RESULTS_DIR,
    CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS,
    OBFUSC_RESULTS_DIR,
    ORI_RESULTS_DIR,
    THREEBENCH_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    THREEBENCH_BENCHMARK_VERIFIED_ENTRY_POINTS,
    VB_SPECIFIED_TASKIDS,
    VB_VERIFY_FAILED_BLACKLIST,
    VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    VSBHERB_BENCHMARK_VERIFIED_ENTRY_POINTS,
)
from vinv.invariant import parse_invariant_items
from vinv.proof import AutoverusProofFile, ObfsProofFile, OneStepProofFile, ProofFile
from vinv.utils import check_status


def dump_ori_results_dir():
    """
    Dump the results directory if it is empty. Copy from the original results
    directory to the new one. Also prepare the deghosted files.
    """
    # dump ori results dir
    for benchmark, entry_point in CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS.items():
        for path in entry_point.glob("**/*.rs"):
            # exclude files like "*_v{0-9}*.rs" files using regex
            if "_v" in path.name:
                continue
            if path.is_file():
                task_dir = ORI_RESULTS_DIR / f"verusbench_{benchmark}_{path.stem}"
                task_dir.mkdir(parents=True, exist_ok=True)
                # copy the file to the task directory
                shutil.copy(path, task_dir / "verified.rs")
                vb_unverified_file = (
                    CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS[benchmark] / path.name
                )
                assert (
                    vb_unverified_file.is_file()
                ), f"Unverified file {vb_unverified_file} does not exist."
                # copy the unverified file to the task directory
                shutil.copy(vb_unverified_file, task_dir / "unverified.rs")
                # deghost the verified file to raw
                deghosted_raw_file = task_dir / "deghosted_raw.rs"
                lynette.code_deghost(
                    str(task_dir / "verified.rs"),
                    str(deghosted_raw_file),
                    deghost_mode="raw",
                    run_fmt=True,
                )


def get_all_vb_proofs(
    verified_proof: bool = True,
    use_specified_taskids: bool = True,
    with_invariant: bool = False,
    remove_blacklisted: bool = True,
    source: Literal["CLEANED_VB", "ADDITIONAL", "THREEBENCH", "VSBHERB"] = "CLEANED_VB",
) -> List[ProofFile]:
    """
    Get all VerusBench proofs from the specified entry points.
    """
    # max-depth=1, .rs file only
    all_proofs = []
    if source == "CLEANED_VB":
        benchmark_entry_points = (
            CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS
            if verified_proof
            else CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS
        )
    elif source == "ADDITIONAL":
        benchmark_entry_points = (
            ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS
            if verified_proof
            else ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS
        )
    elif source == "THREEBENCH":
        benchmark_entry_points = (
            THREEBENCH_BENCHMARK_VERIFIED_ENTRY_POINTS
            if verified_proof
            else THREEBENCH_BENCHMARK_UNVERIFIED_ENTRY_POINTS
        )
    elif source == "VSBHERB":
        benchmark_entry_points = (
            VSBHERB_BENCHMARK_VERIFIED_ENTRY_POINTS
            if verified_proof
            else VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS
        )
    else:
        raise ValueError(
            f"Unknown source: {source}. Expected 'CLEANED_VB', 'ADDITIONAL', 'THREEBENCH', or 'VSBHERB'"
        )
    for benchmark, entry_point in benchmark_entry_points.items():
        for path in entry_point.glob("*.rs"):
            if "_v" in path.name:
                continue
            if path.is_file():
                proof_file = ProofFile(path)
                proof_file.source = source
                all_proofs.append(proof_file)

    if with_invariant:
        # Filter proofs that contain invariants
        all_proofs = [proof for proof in all_proofs if proof.contains_invariant()]

    # Task-id and blacklist filters are specific to VerusBench (CLEANED_VB)
    if use_specified_taskids and source == "CLEANED_VB":
        # Filter proofs that are not in the specified task IDs
        all_proofs = [
            proof for proof in all_proofs if proof.task_id in VB_SPECIFIED_TASKIDS
        ]
    if remove_blacklisted and source == "CLEANED_VB":
        # Filter out proofs that are in the blacklist
        all_proofs = [
            proof
            for proof in all_proofs
            if proof.task_id not in VB_VERIFY_FAILED_BLACKLIST
        ]

    logger.info(
        f"Found {len(all_proofs)} {'verified' if verified_proof else 'unverified'} {'proofs with invariants' if with_invariant else 'proofs'} in {source}."
    )

    if source == "CLEANED_VB":
        if not ORI_RESULTS_DIR.exists() or len(list(ORI_RESULTS_DIR.glob("*"))) == 0:
            print(f"Dumping original results directory to {ORI_RESULTS_DIR}...")
            dump_ori_results_dir()

    return all_proofs


def get_subset_of_unverified_vb_proofs(
    num_proofs: int = 50,
    use_specified_taskids: bool = False,
    with_invariant: bool = False,
    remove_blacklisted: bool = True,
    source: Literal["CLEANED_VB", "ADDITIONAL", "THREEBENCH", "VSBHERB"] = "CLEANED_VB",
) -> List[ProofFile]:
    all_proofs = get_all_vb_proofs(
        verified_proof=False,
        use_specified_taskids=use_specified_taskids,
        with_invariant=with_invariant,
        remove_blacklisted=remove_blacklisted,
        source=source,
    )

    random.seed(0)
    return random.sample(all_proofs, num_proofs)


def get_autoverus_failed_proofs(
    use_specified_taskids: bool = True,
    with_invariant: bool = False,
    remove_blacklisted: bool = True,
) -> List[ProofFile]:
    """
    Get failed autoverus output proofs from the specified entry points.
    """
    # max-depth=1, .rs file only
    failed_proofs = []
    for path in AUTOVERUS_RESULTS_DIR.glob("**/autoverus_output.rs"):
        status_file = path.parent / "verify_status.txt"
        if not check_status(status_file, "verification_error"):
            continue
        proof_file = AutoverusProofFile(path)
        failed_proofs.append(proof_file)

    if with_invariant:
        # Filter proofs that contain invariants
        failed_proofs = [proof for proof in failed_proofs if proof.contains_invariant()]

    if use_specified_taskids:
        # Filter proofs that are not in the specified task IDs
        failed_proofs = [
            proof for proof in failed_proofs if proof.task_id in VB_SPECIFIED_TASKIDS
        ]
    if remove_blacklisted:
        # Filter out proofs that are in the blacklist
        failed_proofs = [
            proof
            for proof in failed_proofs
            if proof.task_id not in VB_VERIFY_FAILED_BLACKLIST
        ]

    logger.info(
        f"Found {len(failed_proofs)} failed autoverus proofs {'with invariants' if with_invariant else ''} in VerusBench."
    )

    return failed_proofs


def get_all_obfs_proofs(
    prompt_type: str = "plain",
    model: str = "gpt-4o",
    use_specified_taskids: bool = True,
    remove_blacklisted: bool = True,
    with_invariant: bool = False,
) -> List[ObfsProofFile]:
    """
    Get all successfully obfuscated VerusBench proofs
    """
    obfs_proofs = []
    all_vb_proofs = get_all_vb_proofs(
        use_specified_taskids=use_specified_taskids,
        with_invariant=True,
        remove_blacklisted=remove_blacklisted,
    )
    all_vb_tasks = [proof.task_id for proof in all_vb_proofs]
    for task_id in all_vb_tasks:
        work_dir = OBFUSC_RESULTS_DIR / f"{prompt_type}_{model}" / task_id
        ori_proof_file = [p for p in all_vb_proofs if p.task_id == task_id][0]
        for response_dir in work_dir.glob("response_*"):
            status_file = response_dir / "OBFS_GEN_STATUS.txt"
            if not status_file.is_file():
                raise FileNotFoundError(f"Status file not found in {response_dir}")
            if not check_status(status_file, "OBFS_VERUS_VERIFIED"):
                continue
            obfuscated_formatted_file = response_dir / "obfuscated_formatted.rs"
            obfuscated_proof = ObfsProofFile(
                obfuscated_formatted_file, parent_proof_file=ori_proof_file
            )
            deghosted_unverified_file = response_dir / "deghosted_unverified.rs"
            # check if deghosted_unverified_file is empty
            if (
                not deghosted_unverified_file.is_file()
                or deghosted_unverified_file.stat().st_size == 0
            ):
                raise FileNotFoundError(
                    f"Deghosted unverified file not found or is empty in {response_dir}"
                )
            obfs_proofs.append(obfuscated_proof)

    if with_invariant:
        # Filter proofs that contain invariants
        obfs_proofs = [proof for proof in obfs_proofs if proof.contains_invariant()]
    logger.info(
        f"Found {len(obfs_proofs)} obfuscated proofs {'with invariants' if with_invariant else ''} in VerusBench."
    )
    return obfs_proofs


def get_almost_correct_av_proofs(
    av_failed: bool = True,
) -> List[ProofFile]:
    """
    Get all almost correct autoverus proofs from the specified entry points.
    """
    proof_dir = AUTOVERUS_ALMOST_CORRECT_RESULTS_DIR / (
        "unverified" if av_failed else "verified"
    )
    all_proofs = []
    for path in proof_dir.glob("*.rs"):
        proof_file = OneStepProofFile(path)
        all_proofs.append(proof_file)
    return all_proofs


def main():
    all_proofs = get_all_vb_proofs()
    proofs_with_invariant = [
        proof for proof in all_proofs if proof.contains_invariant()
    ]
    print(f"Total number of proofs: {len(all_proofs)}")
    print(f"Number of proofs with invariant: {len(proofs_with_invariant)}")

    for proof in proofs_with_invariant:
        print(proof)
        invariant_entry_list = proof.parse_invariants()
        for func_id, invariant_entries in invariant_entry_list.items():
            print(f"Function {func_id} has {len(invariant_entries)} invariant entries")
            for entry in invariant_entries:
                print(f"  Invariant entry: {entry.invariants_code}")
                for invariant_item in parse_invariant_items(entry):
                    print(
                        f"    Invariant item: ({invariant_item.invariant_item_start}, {invariant_item.invariant_item_end}) {invariant_item.invariant_item_code}"
                    )

        specification_entry_dict = proof.parse_specifications()
        for func_id, spec_entry in specification_entry_dict.items():
            print(f"Function id {func_id} has specification entry:")
            print(f"  {spec_entry.spec_code}")

        print("-" * 20)


if __name__ == "__main__":
    Fire(main)
