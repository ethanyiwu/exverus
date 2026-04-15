import io
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple

from fire import Fire

# autoverus imports
from generation import Generation
from loguru import logger
from utils import AttrDict, clean_code, insert_loop_isolation

from vinv.config import (
    PIPELINE_DEBUG_RESULTS_DIR,
    PIPELINE_RESULTS_DIR,
    get_autoverus_config_file,
)
from vinv.data.cherrypick import get_all_vb_proofs, get_subset_of_unverified_vb_proofs
from vinv.gen.cost_report import (
    finalize_task_cost_report,
    initialize_task_cost_report,
    merge_task_cost_reports,
)
from vinv.pipeline.cex import cex_iterative_repair
from vinv.pipeline.cex_validation_backend import CexValidationBackend
from vinv.pipeline.iterative import iterative_repair
from vinv.proof import IntermediateProofFile, ProofFile
from vinv.utils import check_status, get_last_attempt_file, json_load
from vinv.verus_utils import (
    get_console_error_msg_from_rustc_out,
    get_verus_errors_score,
    record_verify_status,
    record_verify_status_for_proof_folder,
)


def _repair_steps_suffix(max_repair_attempts: int) -> str:
    return f"{max_repair_attempts}_steps"


def _iterative_repair_dirname(
    repair_strategy: Literal["naive", "compilation"],
    max_repair_attempts: int,
) -> str:
    if repair_strategy == "naive":
        return (
            f"iterative_repair_{repair_strategy}_"
            f"{_repair_steps_suffix(max_repair_attempts)}"
        )
    return f"iterative_repair_{repair_strategy}"


def _cex_repair_dirname(
    cex_generation_strategy: str,
    cex_generalization_strategy: str,
    num_cex: int,
) -> str:
    return f"cex_repair_{cex_generation_strategy}_{cex_generalization_strategy}_{num_cex}"


def get_last_repair_file(work_dir: Path, init_gen_file_name: str) -> Path:
    """
    Traverse init_gen, naive_repair, compilation_repair directories and get the last repair file.
    """
    init_gen_verify_status = json_load(work_dir / "init_gen" / "verify_status.json")[
        init_gen_file_name
    ]["status"]
    if init_gen_verify_status == "verification_pass":
        return work_dir / "init_gen" / init_gen_file_name

    repair_root_patterns = [
        "iterative_repair_naive_*_steps",
        "iterative_repair_naive",
        "iterative_repair_compilation_*_steps",
        "iterative_repair_compilation",
    ]
    for repair_root_pattern in repair_root_patterns:
        for repair_root in sorted(work_dir.glob(repair_root_pattern), reverse=True):
            for repair_dir in sorted(repair_root.iterdir(), reverse=True):
                if not repair_dir.is_dir():
                    continue
                try:
                    last_repair_file = get_last_attempt_file(repair_dir, "repaired.rs")
                except (AssertionError, ValueError):
                    continue
                if last_repair_file.is_file():
                    return last_repair_file

    raise FileNotFoundError(f"No repair file found in {work_dir}")


def init_generation(
    unverified_proof: ProofFile,
    init_gen_dir: Path,
    model_id: str = "gpt-4o",
) -> IntermediateProofFile:
    gt_proof = ProofFile(
        Path(unverified_proof.path.as_posix().replace("unverified", "verified"))
    )

    proof_files = list(init_gen_dir.glob("gen_*.rs"))
    logger.info(
        f"Initial generation directory: {init_gen_dir}, existing proofs: {len(proof_files)}"
    )
    if len(proof_files) == 1:
        logger.info(
            f"Already generated 1 proof in {init_gen_dir}. Skipping generation."
        )
        return IntermediateProofFile(proof_files[0], gt_proof)
    elif len(proof_files) > 0:
        raise ValueError(
            f"Found {len(proof_files)} generated proofs in \
            {init_gen_dir}. Expected 1."
        )

    ori_code = unverified_proof.path.read_text()
    autoverus_config = AttrDict(json_load(get_autoverus_config_file(model_id)))
    # refinement = Refinement(autoverus_config, logger)
    phase1_examples = ["3", "6", "7"]
    generation = Generation(
        autoverus_config,
        logger,
        phase1_examples=phase1_examples,
        repair_uniform=True,
    )
    codes = generation.direct_inference(
        ori_code,
        temp=1.0,
    )
    init_gen_dir.mkdir(parents=True, exist_ok=True)
    code = clean_code(codes[0])
    # add #[verifier::loop_isolation(false)]
    if "loop_isolation(false)" not in code:
        code = insert_loop_isolation(code)
    gen_proof_path = init_gen_dir / "gen_0.rs"
    gen_proof_path.write_text(code)
    return IntermediateProofFile(gen_proof_path, gt_proof)


def reason_failing_proof(
    proof: ProofFile,
):
    """
    Given a failed proof, reason it's because of wrong invariants or too weak
    and not inductive invariants.
    """
    assert not proof.verified, f"Proof {proof.path} is already verified."
    verus_errors, score = get_verus_errors_score(proof.path)
    assert len(verus_errors) > 0, f"Proof {proof.path} has no failures: {verus_errors}"
    # log all failures
    print("=" * 80)
    print(f"Proof {proof.path} score: {score}")
    print(f"Proof {proof.path} has {len(verus_errors)} failures.")
    for verus_error in verus_errors:
        print("*" * 80)
        print(f"Error Type: {verus_error.error}")
        print(f"At: {verus_error.spans}")
        print(f"Error text: {verus_error.error_text}")


def update_repair_status(
    repair_status: Dict[str, Dict[str, Any]],
    proof_id: str,
    verification_status: str,
    last_phase: str,
    last_repaired_code_path: Path | None,
) -> None:
    """
    Update the repair status dictionary with the latest status.
    """
    repair_status[proof_id] = {
        "verification_status": verification_status,
        "last_phase": last_phase,
        "last_repaired_code_path": last_repaired_code_path,
    }


def attempt_cex_repair(
    init_gen_id: str,
    error_proof: IntermediateProofFile,
    work_dir: Path,
    console_error_msg: str,
    model: str,
    max_repair_attempts: int,
    cex_generation_strategy: str,
    cex_generalization_strategy: str,
    original_proof_file: Path | None = None,
    num_cex: int = 10,
    cex_validation_backend: CexValidationBackend = "v2",
) -> Tuple[Path | None, bool, bool]:
    """
    Attempt CEX-based repair on a proof.
    Returns:
        - Path | None: Path to the last repaired code if any
        - bool: Whether the repair was successful
        - bool: Whether there's still a compilation error
    """
    cex_repair_dir = (
        work_dir
        / _cex_repair_dirname(
            cex_generation_strategy,
            cex_generalization_strategy,
            num_cex,
        )
        / init_gen_id
    )
    cex_repair_dir.mkdir(parents=True, exist_ok=True)
    cex_repair_status_file = cex_repair_dir / "cex_repair_status.txt"
    backend_marker_file = cex_repair_dir / "cex_validation_backend.txt"

    if (
        cex_repair_status_file.exists()
        and backend_marker_file.exists()
        and backend_marker_file.read_text(encoding="utf-8").strip()
        == cex_validation_backend
    ):
        logger.info(
            f"Skipping CEX repair for {error_proof.path} as it has already been tried to repair."
        )
        return (
            get_last_attempt_file(cex_repair_dir, "repaired.rs"),
            check_status(cex_repair_status_file, "verification_pass"),
            check_status(cex_repair_status_file, "compilation_error"),
        )

    try:
        backend_marker_file.write_text(cex_validation_backend, encoding="utf-8")
        # Attempt counter example guided repair
        fixed_proof_path = cex_iterative_repair(
            error_proof_file=error_proof.path,
            console_error_msg=console_error_msg,
            cex_repair_dir=cex_repair_dir,
            original_proof_file=original_proof_file,
            model=model,
            max_try=max_repair_attempts,
            cex_generation_strategy=cex_generation_strategy,
            cex_generalization_strategy=cex_generalization_strategy,
            num_cex=num_cex,
            cex_validation_backend=cex_validation_backend,
        )

        # Check if repair was successful and record status
        if fixed_proof_path and fixed_proof_path.exists():
            # Use the standard record_verify_status function for consistency
            verification_passed = record_verify_status(
                fixed_proof_path, cex_repair_status_file, override=True
            )

            has_compilation_error = check_status(
                cex_repair_status_file, "compilation_error"
            )

            if verification_passed:
                logger.success(f"CEX repair successful for {error_proof.path}")
                return fixed_proof_path, True, False
            else:
                logger.warning(f"CEX repair failed to verify for {error_proof.path}")
                return fixed_proof_path, False, has_compilation_error
        else:
            # CEX repair failed to produce any output
            raise ValueError(
                f"CEX repair failed to produce any output for {error_proof.path}"
            )

    except Exception as e:
        raise ValueError(f"Error during CEX repair for {error_proof.path}: {e}")


def attempt_compilation_repair(
    init_gen_id: str,
    error_proof: IntermediateProofFile,
    work_dir: Path,
    console_error_msg: str,
    model: str,
    max_repair_attempts: int,
    original_proof_file: Path | None = None,
) -> Tuple[Path | None, bool, bool]:
    """
    Attempt compilation repair on a proof.
    Returns:
        - Path | None: Path to the last repaired code if any
        - bool: Whether the repair was successful
        - bool: Whether there's still a compilation error
    """
    compilation_repair_dir = (
        work_dir
        / _iterative_repair_dirname("compilation", max_repair_attempts)
        / init_gen_id
    )
    compilation_repair_dir.mkdir(parents=True, exist_ok=True)
    compilation_repair_status_file = (
        compilation_repair_dir / "compilation_repair_status.txt"
    )

    if compilation_repair_status_file.exists():
        logger.info(
            f"Skipping compilation iterative repair for {error_proof.path} as it has already been tried to repair."
        )
        return (
            get_last_attempt_file(compilation_repair_dir, "repaired.rs"),
            check_status(compilation_repair_status_file, "verification_pass"),
            check_status(compilation_repair_status_file, "compilation_error"),
        )

    try:
        last_repaired_code_path, repaired = iterative_repair(
            error_proof,
            console_error_msg,
            compilation_repair_dir,
            model=model,
            max_try=max_repair_attempts,
            repair_strategy="compilation",
            original_proof_file=original_proof_file,
        )
    except KeyboardInterrupt:
        # remove the repair directory if interrupted
        if compilation_repair_dir.exists():
            shutil.rmtree(compilation_repair_dir)
        raise KeyboardInterrupt(
            f"Compilation iterative repair interrupted for {error_proof.path}. Repair directory removed."
        )

    is_verified = check_status(compilation_repair_status_file, "verification_pass")
    has_compilation_error = check_status(
        compilation_repair_status_file, "compilation_error"
    )

    if is_verified:
        logger.info(
            f"Compilation iterative repair for {error_proof.path} verified: {repaired}"
        )
    elif has_compilation_error:
        logger.info(
            f"Compilation iterative repair for {error_proof.path} failed, still in compilation error."
        )

    return last_repaired_code_path, is_verified, has_compilation_error


def attempt_naive_repair(
    init_gen_id: str,
    error_proof: IntermediateProofFile,
    work_dir: Path,
    init_console_error_msg: str,
    model: str,
    max_repair_attempts: int,
    original_proof_file: Path | None = None,
) -> Tuple[Path | None, bool, bool]:
    """
    Attempt naive repair on a proof.
    Returns:
        - Path | None: Path to the last repaired code if any
        - bool: Whether the repair was successful
        - bool: Whether there's a compilation error
    """
    naive_repair_dir = (
        work_dir / _iterative_repair_dirname("naive", max_repair_attempts) / init_gen_id
    )
    naive_repair_status_file = naive_repair_dir / "naive_repair_status.txt"
    naive_repair_dir.mkdir(parents=True, exist_ok=True)

    if naive_repair_status_file.exists():
        logger.info(
            f"Skipping naive iterative repair for {error_proof.path} as it has already been tried to repair."
        )
        return (
            get_last_attempt_file(naive_repair_dir, "repaired.rs"),
            check_status(naive_repair_status_file, "verification_pass"),
            check_status(naive_repair_status_file, "compilation_error"),
        )

    try:
        last_repaired_code_path, repaired = iterative_repair(
            error_proof,
            init_console_error_msg,
            naive_repair_dir,
            model=model,
            max_try=max_repair_attempts,
            repair_strategy="naive",
            original_proof_file=original_proof_file,
        )
    except KeyboardInterrupt:
        # remove the repair directory if interrupted
        if naive_repair_dir.exists():
            shutil.rmtree(naive_repair_dir)
        raise KeyboardInterrupt(
            f"Naive iterative repair interrupted for {error_proof.path}. Repair directory removed."
        )

    is_verified = check_status(naive_repair_status_file, "verification_pass")
    has_compilation_error = check_status(naive_repair_status_file, "compilation_error")

    if is_verified:
        logger.info(
            f"Naive iterative repair for {error_proof.path} verified: {repaired}"
        )
    elif has_compilation_error:
        logger.info(
            f"Naive iterative repair for {error_proof.path} failed with compilation error."
        )
    else:
        logger.info(
            f"Naive iterative repair for {error_proof.path} failed with verification error."
        )

    return last_repaired_code_path, is_verified, has_compilation_error


def check_initial_verification(
    unverified_proof: ProofFile,
    work_dir: Path,
    model: str,
) -> Tuple[bool, IntermediateProofFile, Path | None, str]:
    """
    Check initial verification status for a proof.
    Returns:
        - bool: Whether the generated proof is verified
        - IntermediateProofFile: The single generated proof
        - Path | None: Path to the verified proof if any
        - str: Console error message extracted from rustc output
    """
    # initial attempt of proof generation
    init_gen_proof = init_generation(
        unverified_proof,
        work_dir / "init_gen",
        model_id=model,
    )

    logger.info("Generated initial proof")

    # check status of the generated proof
    init_gen_verify_status_file = work_dir / "init_gen" / "verify_status.json"
    any_verified = record_verify_status_for_proof_folder(
        work_dir / "init_gen",
        init_gen_verify_status_file,
    )

    logger.info(
        f"Initial generation for {unverified_proof.full_id} verified: {any_verified}"
    )

    init_gen_verify_status = json_load(init_gen_verify_status_file)
    proof_status = init_gen_verify_status.get(init_gen_proof.path.name, {})
    init_console_error_msg = get_console_error_msg_from_rustc_out(
        proof_status.get("rustc_out", "")
    )
    verified_proof_path = init_gen_proof.path if any_verified else None

    return any_verified, init_gen_proof, verified_proof_path, init_console_error_msg


def _status_suffix(
    *,
    ablation: bool,
    cex_generation_strategy: str,
    cex_generalization_strategy: str,
    num_cex: int,
    max_repair_attempts: int,
) -> str:
    if ablation:
        return f"naive_{_repair_steps_suffix(max_repair_attempts)}"
    return f"{cex_generation_strategy}_{cex_generalization_strategy}_{num_cex}"


def _process_proof_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the per-proof pipeline in an isolated process and capture all logs.
    Returns dict with: full_id, status (dict|None), logs (str), cost_report_path (str), error (optional str)
    """
    from vinv.proof import ProofFile  # local import to keep pickling simple

    full_id: str = task["full_id"]
    work_dir = Path(task["work_dir"])
    model: str = task["model"]
    cex_generation_strategy: str = task["cex_generation_strategy"]
    cex_generalization_strategy: str = task["cex_generalization_strategy"]
    num_cex: int = task["num_cex"]
    cex_validation_backend: CexValidationBackend = task.get(
        "cex_validation_backend", "v2"
    )
    ablation: bool = task.get("ablation", False)
    max_repair_attempts: int = task.get("max_repair_attempts", 5)
    unverified_path = Path(task["unverified_path"])
    source: str = task.get("source", "unknown")
    task_started_at = time.time()
    status_suffix = _status_suffix(
        ablation=ablation,
        cex_generation_strategy=cex_generation_strategy,
        cex_generalization_strategy=cex_generalization_strategy,
        num_cex=num_cex,
        max_repair_attempts=max_repair_attempts,
    )
    cost_report_path = initialize_task_cost_report(
        report_path=work_dir / f"llm_cost_report_{status_suffix}.json",
        task_metadata={
            "task_full_id": full_id,
            "work_dir": str(work_dir),
            "model": model,
            "source": source,
            "ablation": ablation,
            "max_repair_attempts": max_repair_attempts,
            "cex_generation_strategy": cex_generation_strategy,
            "cex_generalization_strategy": cex_generalization_strategy,
            "num_cex": num_cex,
            "cex_validation_backend": cex_validation_backend,
            "status_suffix": status_suffix,
        },
    )

    buf = io.StringIO()
    sink_id = logger.add(buf, enqueue=False, backtrace=False, diagnose=False)
    status_entry: Dict[str, Any] | None = None
    err_msg: str | None = None

    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            logger.info(f"***** Processing {full_id} *****")
            unverified_proof = ProofFile(unverified_path)

            (
                any_verified,
                init_gen_proof,
                verified_proof_path,
                init_console_error_msg,
            ) = check_initial_verification(unverified_proof, work_dir, model)

            repair_status: Dict[str, Dict[str, Any]] = {}
            if any_verified:
                update_repair_status(
                    repair_status,
                    unverified_proof.full_id,
                    "verification_pass",
                    "init_gen",
                    verified_proof_path,
                )
                logger.info(
                    f"Skipping naive iterative repair for {unverified_proof.full_id} as the init gen has already passed the verification."
                )
            else:
                if ablation:
                    (
                        last_repaired_code_path,
                        is_verified,
                        has_compilation_error,
                    ) = attempt_naive_repair(
                        init_gen_proof.path.stem,
                        init_gen_proof,
                        work_dir,
                        init_console_error_msg,
                        model,
                        max_repair_attempts,
                        original_proof_file=unverified_proof.path,
                    )
                    last_phase = "naive_repair"
                else:
                    # main pipeline with CEX repair
                    (
                        last_repaired_code_path,
                        is_verified,
                        has_compilation_error,
                    ) = attempt_cex_repair(
                        init_gen_proof.path.stem,
                        init_gen_proof,
                        work_dir,
                        init_console_error_msg,
                        model,
                        max_repair_attempts,
                        cex_generation_strategy,
                        cex_generalization_strategy,
                        original_proof_file=unverified_proof.path,
                        num_cex=num_cex,
                        cex_validation_backend=cex_validation_backend,
                    )
                    last_phase = "cex_repair"

                if is_verified:
                    update_repair_status(
                        repair_status,
                        unverified_proof.full_id,
                        "verification_pass",
                        last_phase,
                        last_repaired_code_path,
                    )
                else:
                    update_repair_status(
                        repair_status,
                        unverified_proof.full_id,
                        "compilation_error"
                        if has_compilation_error
                        else "verification_error",
                        last_phase,
                        last_repaired_code_path,
                    )
                    mode_str = "naive" if ablation else "CEX"
                    logger.warning(
                        f"{mode_str} repair failed for {unverified_proof.full_id} {last_repaired_code_path}"
                    )

            if unverified_proof.full_id in repair_status:
                single_status = repair_status[unverified_proof.full_id]
                single_status_serializable = {
                    k: str(v) if isinstance(v, Path) else v
                    for k, v in single_status.items()
                }
                work_dir.mkdir(parents=True, exist_ok=True)
                with open(
                    work_dir / f"repair_status_{status_suffix}.json",
                    "w",
                ) as f:
                    json.dump(
                        {unverified_proof.full_id: single_status_serializable},
                        f,
                        indent=2,
                    )

                status_entry = single_status_serializable

    except Exception as e:
        err_msg = str(e)
        logger.exception(f"Error while processing {full_id}: {e}")
    finally:
        finalize_task_cost_report(
            final_status=status_entry,
            error=err_msg,
            finished_at=time.time(),
        )
        logger.remove(sink_id)

    return {
        "full_id": full_id,
        "status": status_entry,
        "logs": buf.getvalue(),
        "cost_report_path": str(cost_report_path),
        "task_wall_clock_seconds": max(0.0, time.time() - task_started_at),
        **({"error": err_msg} if err_msg else {}),
    }


def main(
    task_type: Literal["ori", "obfs", "failed"] = "ori",
    model: str = "deepseek-chat",
    max_repair_attempts: int = 10,
    cex_generation_strategy: Literal["z3", "simple", "verification"] = "simple",
    cex_generalization_strategy: Literal["simple", "mut_val"] = "simple",
    cex_validation_backend: CexValidationBackend = "v2",
    run_all: bool = False,
    num_cex: int = 10,
    debug: bool = False,
    num_workers: int = 1,
    ablation: bool = False,
    source: Literal["CLEANED_VB", "ADDITIONAL", "THREEBENCH", "VSBHERB"] = "CLEANED_VB",
):
    run_started_at = time.time()
    # {
    # proof_id: {
    # "verification_status": "verification_pass" | "verification_error" | "compilation_error",
    # "last_phase": "init_gen" | "naive_repair" | "compilation_repair" | "cex_repair"
    # "last_repaired_code_path": Path
    # }
    # }
    repair_status = {}
    pipeline_results_dir = PIPELINE_DEBUG_RESULTS_DIR if debug else PIPELINE_RESULTS_DIR
    pipeline_results_dir = pipeline_results_dir / model.split("/")[-1] / source

    if run_all:
        all_unverified_proofs = get_all_vb_proofs(
            verified_proof=False,
            use_specified_taskids=True,
            with_invariant=False,
            remove_blacklisted=True,
            source=source,
        )
    else:
        all_unverified_proofs = get_subset_of_unverified_vb_proofs(
            num_proofs=50,
            use_specified_taskids=False,
            with_invariant=False,
            remove_blacklisted=True,
            source=source,
        )

    if debug:
        target_task_ids = ["verusbench_diffy_brs1", "verusbench_mbpp_task_id_133"]
        all_unverified_proofs = [
            p for p in all_unverified_proofs if p.full_id in target_task_ids
        ]

    tasks: List[Dict[str, Any]] = []
    for unverified_proof in all_unverified_proofs:
        work_dir = pipeline_results_dir / unverified_proof.full_id
        tasks.append(
            {
                "full_id": unverified_proof.full_id,
                "unverified_path": str(unverified_proof.path),
                "work_dir": str(work_dir),
                "model": model,
                "max_repair_attempts": max_repair_attempts,
                "cex_generation_strategy": cex_generation_strategy,
                "cex_generalization_strategy": cex_generalization_strategy,
                "cex_validation_backend": cex_validation_backend,
                "num_cex": num_cex,
                "ablation": ablation,
                "source": source,
            }
        )

    results: List[Dict[str, Any]] = []
    if num_workers and num_workers > 1:
        with ProcessPoolExecutor(max_workers=num_workers) as ex:
            futures = [ex.submit(_process_proof_task, t) for t in tasks]
            for fut in futures:
                results.append(fut.result())
    else:
        for t in tasks:
            results.append(_process_proof_task(t))

    for r in results:
        print("=" * 80)
        print(f"Logs for {r['full_id']}")
        print(r.get("logs", ""))
        if r.get("error"):
            logger.error(f"Processing error for {r['full_id']}: {r['error']}")
        if r.get("status"):
            repair_status[r["full_id"]] = r["status"]

    # Also persist a global status file at the model root for all proofs processed in this run
    status_suffix = _status_suffix(
        ablation=ablation,
        cex_generation_strategy=cex_generation_strategy,
        cex_generalization_strategy=cex_generalization_strategy,
        num_cex=num_cex,
        max_repair_attempts=max_repair_attempts,
    )
    global_status_path = (
        pipeline_results_dir / f"global_repair_status_{status_suffix}.json"
    )
    global_status_path.parent.mkdir(parents=True, exist_ok=True)
    serializable_status = {}
    for proof_id, status in repair_status.items():
        serializable_status[proof_id] = {
            k: str(v) if isinstance(v, Path) else v for k, v in status.items()
        }
    # sort by proof_id
    serializable_status = dict(sorted(serializable_status.items(), key=lambda x: x[0]))
    if not global_status_path.is_file():
        logger.info(f"Saving global repair status to {global_status_path}")
        with open(global_status_path, "w") as f:
            json.dump(serializable_status, f, indent=2)

    # Persist the merged per-task LLM cost report for this run.
    aggregated_cost_path = (
        pipeline_results_dir / f"aggregated_llm_cost_{status_suffix}.json"
    )
    task_report_paths = [
        r["cost_report_path"] for r in results if r.get("cost_report_path")
    ]
    logger.info(f"Saving aggregated LLM cost report to {aggregated_cost_path}")
    merge_task_cost_reports(
        report_paths=task_report_paths,
        output_path=aggregated_cost_path,
        run_metadata={
            "task_type": task_type,
            "model": model,
            "max_repair_attempts": max_repair_attempts,
            "cex_generation_strategy": cex_generation_strategy,
            "cex_generalization_strategy": cex_generalization_strategy,
            "cex_validation_backend": cex_validation_backend,
            "run_all": run_all,
            "num_cex": num_cex,
            "debug": debug,
            "num_workers": num_workers,
            "ablation": ablation,
            "source": source,
            "pipeline_results_dir": str(pipeline_results_dir),
            "status_suffix": status_suffix,
        },
        run_started_at=run_started_at,
        run_finished_at=time.time(),
    )


if __name__ == "__main__":
    Fire(main)
