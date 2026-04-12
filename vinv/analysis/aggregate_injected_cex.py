import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fire import Fire

from vinv.analysis.one_step_cex import analyze_try_dir
from vinv.config import PIPELINE_DEBUG_RESULTS_DIR, PIPELINE_RESULTS_DIR
from vinv.data.select_injected import DEFAULT_INJECT_TYPES, filter_injected
from vinv.utils import check_status


def _simple_model_id(model: str) -> str:
    try:
        return model.split("/")[-1]
    except Exception:
        return model


def _find_latest_try_dir(gen_dir: Path) -> Optional[Path]:
    if not gen_dir.is_dir():
        return None
    try_dirs = [
        p for p in gen_dir.iterdir() if p.is_dir() and p.name.startswith("try_")
    ]
    if not try_dirs:
        return None

    def _idx(p: Path) -> int:
        try:
            return int(p.name.split("_")[-1])
        except Exception:
            return -1

    try_dirs.sort(key=_idx, reverse=True)
    return try_dirs[0]


def _find_gen_dir(
    task_dir: Path,
    cex_generation_strategy: str,
    cex_generalization_strategy: str,
    num_cex: int,
    init_gen_id: str = "gen_0",
) -> Optional[Path]:
    base = (
        task_dir
        / f"cex_repair_{cex_generation_strategy}_{cex_generalization_strategy}_{num_cex}"
        / init_gen_id
    )
    return base if base.is_dir() else None


def _resolve_task_dir(
    pipeline_root: Path, task_id: str, inject_type: str
) -> Optional[Path]:
    # Prefer exact match
    exact = pipeline_root / f"{task_id}_{inject_type}"
    if exact.is_dir():
        return exact
    # Fallback: search for directory names containing task_id and ending with _inject_type
    try:
        for d in pipeline_root.iterdir():
            if not d.is_dir():
                continue
            name = d.name
            if name.endswith(f"_{inject_type}") and task_id in name:
                return d
    except Exception:
        pass
    return None


def aggregate_injected(
    model: str = "gpt-4o",
    inject_types: Optional[List[str]] = None,
    enforce_one_error: bool = False,
    cex_generation_strategy: str = "z3",
    cex_generalization_strategy: str = "mut_val",
    num_cex: int = 10,
    debug: bool = False,
    include_per_task: bool = False,
    verbose: bool = False,
    out: Optional[str] = None,
) -> Dict[str, Any]:
    if inject_types is None:
        inject_types = [t for t in DEFAULT_INJECT_TYPES]

    selected = filter_injected(
        model=model,
        inject_types=inject_types,
        enforce_one_error=enforce_one_error,
        verbose=False,
    )

    pipeline_root = (
        (PIPELINE_DEBUG_RESULTS_DIR if debug else PIPELINE_RESULTS_DIR)
        / _simple_model_id(model)
        / "INJECTED"
    )

    total_generated = 0
    total_validated = 0
    # Buckets by blocked fraction over validated CEXs
    # - no_validated:         validated == 0 (aka 0_0)
    # - blocked_rate_0:       validated > 0 and blocked == 0        (0%)
    # - blocked_rate_nonzero: validated > 0 and blocked > 0         (0-100% or 100%)
    bucket_counts = {
        "no_validated": {
            "mutants": 0,
            "tasks": set(),
            "mutants_verified": 0,
            "tasks_verified": set(),
        },
        "blocked_rate_0": {
            "mutants": 0,
            "tasks": set(),
            "mutants_verified": 0,
            "tasks_verified": set(),
        },
        "blocked_rate_nonzero": {
            "mutants": 0,
            "tasks": set(),
            "mutants_verified": 0,
            "tasks_verified": set(),
        },
    }
    per_task: List[Dict[str, Any]] = []
    num_with_task_dir = 0
    num_with_gen_dir = 0
    num_with_try_dir = 0

    for rec in selected:
        task_id = rec.get("task_id")  # e.g., inv_inject_diffy_ms1
        inj = rec.get("inject_type")  # e.g., strengthen_invariant
        task_dir = _resolve_task_dir(pipeline_root, task_id, inj)
        if not task_dir:
            if verbose:
                print(f"missing task_dir for {task_id}/{inj} under {pipeline_root}")
            continue
        num_with_task_dir += 1
        gen_dir = _find_gen_dir(
            task_dir,
            cex_generation_strategy=cex_generation_strategy,
            cex_generalization_strategy=cex_generalization_strategy,
            num_cex=num_cex,
            init_gen_id="gen_0",
        )
        if not gen_dir:
            if verbose:
                print(f"missing gen_dir for {task_dir}")
            continue
        num_with_gen_dir += 1

        try_dir = _find_latest_try_dir(gen_dir)
        if not try_dir:
            if verbose:
                print(f"missing try_dir under {gen_dir}")
            continue
        num_with_try_dir += 1

        summary = analyze_try_dir(str(try_dir), out=None, quiet=True)
        num_gen = int(summary.get("num_cex_generated") or 0)
        num_val = int(summary.get("num_cex_validated") or 0)
        total_generated += num_gen
        total_validated += num_val

        # Bucketize per-mutant blocked counts against validated CEXs for this task
        for m in summary.get("mutants", []) or []:
            try:
                blocked = int(m.get("blocked_count") or 0)
            except Exception:
                blocked = 0
            try:
                validated = int(m.get("num_cex") or 0)
            except Exception:
                validated = 0

            # Determine bucket key based on ratio
            if validated <= 0:
                key = "no_validated"
            elif blocked <= 0:
                key = "blocked_rate_0"
            else:
                key = "blocked_rate_nonzero"

            # Check if this mutant actually passes verification
            verified = False
            cid = m.get("candidate_id")
            if cid:
                vs_file = Path(try_dir) / "mut_val_mutants" / cid / "verify_status.txt"
                try:
                    verified = check_status(vs_file, "verification_pass")
                except Exception:
                    verified = False

            # Increment counts
            bucket_counts[key]["mutants"] += 1
            bucket_counts[key]["tasks"].add(task_dir.name)
            if verified:
                bucket_counts[key]["mutants_verified"] += 1
                bucket_counts[key]["tasks_verified"].add(task_dir.name)

        if include_per_task:
            per_task.append(
                {
                    "full_id": task_dir.name,
                    "try_dir": str(try_dir),
                    "num_cex_generated": num_gen,
                    "num_cex_validated": num_val,
                    "mutants": summary.get("mutants", []),
                }
            )

    # finalize bucket stats (convert task sets to counts)
    mutant_blocking_by_validated = {}
    for key, val in bucket_counts.items():
        mutants = int(val["mutants"]) if isinstance(val.get("mutants"), int) else 0
        tasks = len(val.get("tasks", set()))
        mutants_verified = int(val.get("mutants_verified", 0))
        tasks_verified = len(val.get("tasks_verified", set()))
        rate = (mutants_verified / mutants) if mutants else 0.0
        pct = rate * 100.0
        task_verified_rate = (tasks_verified / tasks) if tasks else 0.0
        task_verified_pct = task_verified_rate * 100.0
        mutant_blocking_by_validated[key] = {
            "mutants": mutants,
            "tasks": tasks,
            "mutants_verified": mutants_verified,
            "tasks_verified": tasks_verified,
            "mutants_verified_pct": pct,
            "tasks_verified_pct": task_verified_pct,
        }

    result: Dict[str, Any] = {
        "model": model,
        "num_tasks": len(selected),
        "num_tasks_with_results_dir": num_with_task_dir,
        "num_tasks_with_gen_dir": num_with_gen_dir,
        "num_tasks_with_try_dir": num_with_try_dir,
        "total_cex_generated": total_generated,
        "total_cex_validated": total_validated,
        "mutant_blocking_by_validated": mutant_blocking_by_validated,
    }
    if include_per_task:
        result["per_task"] = per_task

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


def main(
    model: str = "gpt-4o",
    inject_types: Optional[List[str]] = None,
    enforce_one_error: bool = False,
    cex_generation_strategy: str = "z3",
    cex_generalization_strategy: str = "mut_val",
    num_cex: int = 10,
    debug: bool = False,
    include_per_task: bool = False,
    out: Optional[str] = None,
):
    return aggregate_injected(
        model=model,
        inject_types=inject_types,
        enforce_one_error=enforce_one_error,
        cex_generation_strategy=cex_generation_strategy,
        cex_generalization_strategy=cex_generalization_strategy,
        num_cex=num_cex,
        debug=debug,
        include_per_task=include_per_task,
        out=out,
    )


if __name__ == "__main__":
    Fire(main)
