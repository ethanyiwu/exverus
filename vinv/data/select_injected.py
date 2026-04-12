import json
from pathlib import Path
from typing import Dict, List, Optional

from fire import Fire
from loguru import logger

from vinv.config import INV_INJECT_RESULTS_DIR
from vinv.data.invariant_inject import check_one_invariant_diff_structural
from vinv.proof import InjectedProofFile

DEFAULT_INJECT_TYPES = [
    "strengthen_invariant",
    "weaken_invariant",
    # "add_invariant",
    "remove_invariant",
]


def _load_result_json(result_path: Path) -> Optional[Dict]:
    try:
        if not result_path.is_file() or result_path.stat().st_size == 0:
            return None
        return json.loads(result_path.read_text())
    except Exception as e:
        logger.warning(f"Failed to load result.json at {result_path}: {e}")
        return None


def filter_injected(
    model: str = "gpt-4o",
    inject_types: Optional[List[str]] = None,
    enforce_one_error: bool = False,
    verbose: bool = True,
) -> List[Dict]:
    """
    Scan INV_INJECT_RESULTS_DIR/<model> and select injected proofs that satisfy:
    1) is indeed buggy; 2) the diff is exactly one invariant; 3) expected error appears.

    Returns a list of records with fields: task_id, inject_type, injected_path, verify_status, error_types, result_path.
    """
    root = INV_INJECT_RESULTS_DIR / f"{model}"
    if inject_types is None:
        inject_types = DEFAULT_INJECT_TYPES

    if not root.exists():
        logger.warning(f"Root directory not found: {root}")
        # List available model dirs under inv_inject for convenience
        if INV_INJECT_RESULTS_DIR.exists():
            try:
                models_available = [
                    p.name for p in INV_INJECT_RESULTS_DIR.iterdir() if p.is_dir()
                ]
                logger.info(
                    f"Available models under {INV_INJECT_RESULTS_DIR}: {models_available}"
                )
            except Exception:
                pass
        return []

    selected: List[Dict] = []
    total_candidates = 0
    reasons: Dict[str, int] = {
        "no_result": 0,
        "not_buggy": 0,
        "not_one_invariant": 0,
        "non_inv_changes": 0,
        "wrong_changed_groups": 0,
        "expected_error_missing": 0,
        "wrong_error_types": 0,
    }

    for task_dir in sorted(root.iterdir()):
        if not task_dir.is_dir():
            continue

        for inject_type in inject_types:
            cand_dir = task_dir / inject_type
            result_path = cand_dir / "result.json"
            injected_path = cand_dir / "injected.rs"
            if not result_path.exists():
                reasons["no_result"] += 1
                continue

            result = _load_result_json(result_path)
            if not result:
                reasons["no_result"] += 1
                continue

            is_buggy = bool(result.get("is_buggy"))
            one_inv = bool(result.get("one_invariant_diff"))
            changed_groups = result.get("changed_invariant_groups")
            non_inv_changes = result.get("non_invariant_changes")
            expected_error_found = bool(result.get("expected_error_found"))

            total_candidates += 1

            # Enforce exactly one invariant group changed and zero non-invariant edits
            one_inv_strict = (
                one_inv
                and changed_groups == 1
                and (non_inv_changes == 0 or non_inv_changes is None)
            )

            # If stored flags say it's not one-invariant, recompute structurally
            # from the artifacts (gt.rs, injected.rs).
            if not one_inv_strict:
                try:
                    gt_path = cand_dir / "gt.rs"
                    inj_path = cand_dir / "injected.rs"
                    if gt_path.exists() and inj_path.exists():
                        ok, details = check_one_invariant_diff_structural(
                            gt_path, gt_path.read_text(), inj_path.read_text()
                        )
                        if (
                            ok
                            and details.get("changed_invariant_groups") == 1
                            and details.get("non_invariant_changes") == 0
                        ):
                            one_inv = True
                            changed_groups = 1
                            non_inv_changes = 0
                            one_inv_strict = True
                except Exception as e:
                    if verbose:
                        logger.debug(
                            f"recompute failed for {task_dir.name}/{inject_type}: {e}"
                        )

            if (
                is_buggy
                and one_inv_strict
                and expected_error_found
                and (not enforce_one_error or len(result.get("error_types")) == 1)
            ):
                selected.append(
                    {
                        "task_id": task_dir.name,
                        "inject_type": inject_type,
                        "injected_path": str(injected_path),
                        "verify_status": result.get("verify_status"),
                        "error_types": result.get("error_types"),
                        "result_path": str(result_path),
                    }
                )
            else:
                if not is_buggy:
                    reasons["not_buggy"] += 1
                    if verbose:
                        logger.debug(
                            f"skip {task_dir.name}/{inject_type}: not buggy (status={result.get('verify_status')})"
                        )
                elif not one_inv:
                    reasons["not_one_invariant"] += 1
                    if verbose:
                        logger.debug(
                            f"skip {task_dir.name}/{inject_type}: one_invariant_diff=False"
                        )
                elif changed_groups != 1:
                    reasons["wrong_changed_groups"] += 1
                    if verbose:
                        logger.debug(
                            f"skip {task_dir.name}/{inject_type}: changed_groups={changed_groups}"
                        )
                elif non_inv_changes not in (0, None):
                    reasons["non_inv_changes"] += 1
                    if verbose:
                        logger.debug(
                            f"skip {task_dir.name}/{inject_type}: non_inv_changes={non_inv_changes}"
                        )
                elif not expected_error_found:
                    reasons["expected_error_missing"] += 1
                    if verbose:
                        logger.debug(
                            f"skip {task_dir.name}/{inject_type}: expected_error_found=False; errors={result.get('error_types')}"
                        )
                elif len(result.get("error_types")) != 1 and enforce_one_error:
                    reasons["wrong_error_types"] += 1
                    if verbose:
                        logger.debug(
                            f"skip {task_dir.name}/{inject_type}: wrong_error_types={result.get('error_types')}"
                        )

    if verbose:
        logger.info(
            f"Scanned tasks under {root}: candidates={total_candidates}, selected={len(selected)}; reasons={reasons}"
        )

    return selected


def get_selected_injected_proofs(
    model: str = "gpt-4o",
    inject_types: Optional[List[str]] = [
        "strengthen_invariant",
        "weaken_invariant",
        "add_invariant",
        "remove_invariant",
    ],
    verbose: bool = False,
    enforce_one_error: bool = False,
) -> List[InjectedProofFile]:
    selected = filter_injected(
        model=model,
        inject_types=inject_types,
        verbose=verbose,
        enforce_one_error=enforce_one_error,
    )
    return [InjectedProofFile(Path(p.get("injected_path"))) for p in selected]


def main(
    model: str = "gpt-4o",
    inject_types: Optional[List[str]] = [
        "strengthen_invariant",
        "weaken_invariant",
        "add_invariant",
        "remove_invariant",
    ],
    write_manifest: bool = False,
    verbose: bool = False,
    print_errors: bool = True,
    enforce_one_error: bool = False,
):
    selected = filter_injected(
        model=model,
        inject_types=inject_types,
        verbose=verbose,
        enforce_one_error=enforce_one_error,
    )
    logger.info(f"Selected {len(selected)} injected proofs for model={model}")
    if write_manifest:
        out_dir = INV_INJECT_RESULTS_DIR / f"{model}"
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest = out_dir / "selected.json"
        manifest.write_text(json.dumps(selected, indent=2))
        logger.info(f"Wrote selection manifest to {manifest}")

    if print_errors:
        for rec in selected:
            task_id = rec.get("task_id")
            inject_type = rec.get("inject_type")
            error_types = rec.get("error_types") or []
            try:
                errs = ", ".join(error_types)
            except Exception:
                errs = str(error_types)
            print(f"{task_id}/{inject_type}: {errs}")


if __name__ == "__main__":
    Fire(main)
