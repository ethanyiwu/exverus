import io
import json
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, Literal

from fire import Fire
from loguru import logger

from vinv.config import PIPELINE_DEBUG_RESULTS_DIR, PIPELINE_RESULTS_DIR
from vinv.data.cherrypick import get_almost_correct_av_proofs
from vinv.data.select_injected import get_selected_injected_proofs
from vinv.pipeline.main import attempt_cex_repair
from vinv.pipeline.cex_validation_backend import CexValidationBackend
from vinv.utils import json_load
from vinv.verus_utils import (
    get_console_error_msg_from_rustc_out,
    record_verify_status_for_proof_folder,
)


def _process_proof_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single proof in an isolated process and return its status entry.
    Returns dict with: full_id, status (dict|None), error (optional str)
    """
    full_id: str = task["full_id"]
    work_dir = Path(task["work_dir"])
    model: str = task["model"]
    max_repair_attempts: int = task["max_repair_attempts"]
    cex_generation_strategy: str = task["cex_generation_strategy"]
    cex_generalization_strategy: str = task["cex_generalization_strategy"]
    num_cex: int = task["num_cex"]
    cex_validation_backend: CexValidationBackend = task.get(
        "cex_validation_backend", "v2"
    )
    ablation: bool = task["ablation"]
    source_path = Path(task["source_path"])  # original proof file

    buf = io.StringIO()
    sink_id = logger.add(buf, enqueue=False, backtrace=False, diagnose=False)
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            logger.info(f"***** Processing {full_id} *****")
            init_gen_dir = work_dir / "init_gen"
            init_gen_dir.mkdir(parents=True, exist_ok=True)
            init_gen_file = init_gen_dir / "gen_0.rs"
            init_gen_file.write_text(source_path.read_text())

            # check status of the generated proof
            init_gen_verify_status_file = work_dir / "init_gen" / "verify_status.json"
            record_verify_status_for_proof_folder(
                init_gen_dir,
                init_gen_verify_status_file,
            )

            init_gen_verify_status = json_load(init_gen_verify_status_file)
            proof_status = init_gen_verify_status.get(init_gen_file.name, {})
            init_console_error_msg = get_console_error_msg_from_rustc_out(
                proof_status.get("rustc_out", "")
            )

            class _P:
                def __init__(self, p: Path):
                    self.path = p

            (
                last_repaired_code_path,
                is_verified,
                has_compilation_error,
            ) = attempt_cex_repair(
                "gen_0",
                _P(source_path),  # keep behavior: use original file context
                work_dir,
                init_console_error_msg,
                model,
                max_repair_attempts,
                cex_generation_strategy,
                cex_generalization_strategy,
                original_proof_file=source_path,
                num_cex=num_cex,
                cex_validation_backend=cex_validation_backend,
            )
            last_phase = "cex_repair"

            if is_verified:
                status_entry = {
                    "verification_status": "verification_pass",
                    "last_phase": last_phase,
                    "last_repaired_code_path": last_repaired_code_path,
                }
            else:
                status_entry = {
                    "verification_status": "compilation_error"
                    if has_compilation_error
                    else "verification_error",
                    "last_phase": last_phase,
                    "last_repaired_code_path": last_repaired_code_path,
                }

            if not is_verified:
                mode_str = "naive" if ablation else "CEX"
                logger.warning(
                    f"{mode_str} repair failed for {full_id} {last_repaired_code_path}"
                )

        # serialize Paths for safe parent-process merge
        serializable_status = {
            k: str(v) if isinstance(v, Path) else v for k, v in status_entry.items()
        }

        return {
            "full_id": full_id,
            "status": serializable_status,
            "logs": buf.getvalue(),
        }

    except Exception as e:
        logger.exception(f"Error while processing {full_id}: {e}")
        return {
            "full_id": full_id,
            "status": None,
            "error": str(e),
            "logs": buf.getvalue(),
        }
    finally:
        logger.remove(sink_id)


def main(
    model: str = "gpt-4o",
    max_repair_attempts: int = 10,
    cex_generation_strategy: Literal["z3", "simple", "verification"] = "simple",
    cex_generalization_strategy: Literal["simple", "mut_val"] = "simple",
    cex_validation_backend: CexValidationBackend = "v2",
    num_cex: int = 10,
    num_workers: int = 1,
    debug: bool = False,
    ablation: bool = False,
    source: Literal["AV_TRAJ", "INJECTED"] = "INJECTED",
):
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

    if source == "AV_TRAJ":
        proofs = get_almost_correct_av_proofs(av_failed=True)
    elif source == "INJECTED":
        proofs = get_selected_injected_proofs(
            model=model,
            inject_types=[
                "strengthen_invariant",
                "weaken_invariant",
                # "add_invariant",
                "remove_invariant",
            ],
            enforce_one_error=False,
        )
    else:
        raise ValueError(f"Unknown source: {source}")

    tasks = []
    for proof in proofs:
        work_dir = pipeline_results_dir / proof.full_id
        tasks.append(
            {
                "full_id": proof.full_id,
                "source_path": str(proof.path),
                "work_dir": str(work_dir),
                "model": model,
                "max_repair_attempts": max_repair_attempts,
                "cex_generation_strategy": cex_generation_strategy,
                "cex_generalization_strategy": cex_generalization_strategy,
                "cex_validation_backend": cex_validation_backend,
                "num_cex": num_cex,
                "ablation": ablation,
            }
        )

    results = []
    if num_workers and num_workers > 1:
        with ProcessPoolExecutor(max_workers=num_workers) as ex:
            futures = [ex.submit(_process_proof_task, t) for t in tasks]
            for fut in futures:
                results.append(fut.result())
    else:
        for t in tasks:
            results.append(_process_proof_task(t))

    for r in results:
        if r.get("status"):
            repair_status[r["full_id"]] = r["status"]
        if r.get("error"):
            logger.error(f"Processing error for {r['full_id']}: {r['error']}")
        if r.get("logs"):
            print("=" * 80)
            print(f"Logs for {r['full_id']}")
            print(r["logs"])

    # Persist a global status file at the model root for all proofs processed in this run
    status_suffix = (
        "naive"
        if ablation
        else f"{cex_generation_strategy}_{cex_generalization_strategy}"
    )
    global_status_path = (
        pipeline_results_dir / f"global_repair_status_{status_suffix}_{num_cex}.json"
    )
    global_status_path.parent.mkdir(parents=True, exist_ok=True)
    serializable_status: Dict[str, Dict[str, Any]] = {}
    for proof_id, status in repair_status.items():
        serializable_status[proof_id] = {
            k: str(v) if isinstance(v, Path) else v for k, v in status.items()
        }
    # merge with existing if present
    if global_status_path.is_file():
        try:
            with open(global_status_path, "r") as f:
                existing = json.load(f)
            existing.update(serializable_status)
            serializable_status = existing
        except Exception:
            pass
    # sort by proof_id and write
    serializable_status = dict(sorted(serializable_status.items(), key=lambda x: x[0]))
    logger.info(f"Saving global repair status to {global_status_path}")
    with open(global_status_path, "w") as f:
        json.dump(serializable_status, f, indent=2)


if __name__ == "__main__":
    Fire(main)
