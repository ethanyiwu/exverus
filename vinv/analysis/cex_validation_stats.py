"""
Aggregate statistics about CEX validation outcomes and their relation to
per-step error reduction.

Examples:
    python3 -m vinv.analysis.cex_validation_stats \
        results/pipeline/gpt-4o/CLEANED_VB \
        --strategy cex_repair_z3_mut_val_10

    python3 -m vinv.analysis.cex_validation_stats \
        results/pipeline/gpt-4o/CLEANED_VB/verusbench_diffy_brs1 \
        --strategy cex_repair_z3_mut_val_10 \
        --format json
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from vinv.analysis.run_error_stats import find_gen_dirs


COMPILATION_ERROR_SCORE = 10**9


def _read_json_safe(path: Path) -> Optional[Any]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _read_text_safe(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


def _try_attempt_number(try_dir: Path) -> Optional[int]:
    if not try_dir.is_dir() or not try_dir.name.startswith("try_"):
        return None
    try:
        return int(try_dir.name.split("_")[-1])
    except ValueError:
        return None


def _iter_try_dirs(gen_dir: Path) -> List[Path]:
    try_dirs = []
    for child in gen_dir.iterdir():
        attempt = _try_attempt_number(child)
        if attempt is None:
            continue
        try_dirs.append(child)
    try_dirs.sort(key=lambda path: int(path.name.split("_")[-1]))
    return try_dirs


def _normalize_target_error(raw: object) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value:
        return None

    lowered = value.lower()
    if "invariant not satisfied before loop" in lowered:
        return "InvFailFront"
    if "invariant not satisfied at end of loop body" in lowered:
        return "InvFailEnd"
    return value


def _load_trajectory_attempts(gen_dir: Path) -> Dict[int, Dict[str, Any]]:
    data = _read_json_safe(gen_dir / "trajectory.json")
    if not isinstance(data, dict):
        return {}

    out: Dict[int, Dict[str, Any]] = {}
    for iteration in data.get("iterations", []):
        if not isinstance(iteration, dict):
            continue
        attempt = iteration.get("attempt")
        if isinstance(attempt, int):
            out[attempt] = iteration
    return out


def _target_error_for_try(
    try_dir: Path,
    trajectory_attempts: Dict[int, Dict[str, Any]],
) -> Optional[str]:
    attempt = _try_attempt_number(try_dir)
    if attempt is not None:
        iteration = trajectory_attempts.get(attempt, {})
        if isinstance(iteration, dict):
            normalized = _normalize_target_error(iteration.get("target_error"))
            if normalized:
                return normalized

    repair_status = _read_json_safe(try_dir / "repair_status.json")
    if isinstance(repair_status, dict):
        normalized = _normalize_target_error(repair_status.get("error_type"))
        if normalized:
            return normalized

    batch_results = _read_json_safe(try_dir / "harness_before" / "batch_results.json")
    if isinstance(batch_results, list) and batch_results:
        first = batch_results[0]
        if isinstance(first, dict):
            cex = first.get("cex")
            if isinstance(cex, dict):
                normalized = _normalize_target_error(cex.get("error_type"))
                if normalized:
                    return normalized

    return None


def _parse_error_count(text: str) -> Optional[int]:
    if not text:
        return None

    match = re.search(
        r"verification results::\s*(\d+)\s*verified,\s*(\d+)\s*errors", text
    )
    if match:
        try:
            return int(match.group(2))
        except Exception:
            pass

    count = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("error:") and "aborting due to" not in line:
            count += 1
    return count if count > 0 else None


def _error_score_for_stage(try_dir: Path, prefix: str) -> Optional[int]:
    status = _read_text_safe(try_dir / f"{prefix}_verify_status.txt").strip()
    if status == "compilation_error":
        return COMPILATION_ERROR_SCORE
    if status == "verification_pass":
        return 0

    out_count = _parse_error_count(_read_text_safe(try_dir / f"{prefix}_out.txt"))
    if out_count is not None:
        return out_count

    err_count = _parse_error_count(_read_text_safe(try_dir / f"{prefix}_err.txt"))
    if err_count is not None:
        return err_count

    if status == "verification_error":
        # Conservative fallback when the verifier status is known but the exact
        # count is absent from the captured logs.
        return 1

    return None


def _error_improvement_for_try(try_dir: Path) -> tuple[Optional[bool], Optional[int], Optional[int]]:
    before = _error_score_for_stage(try_dir, "input")
    after = _error_score_for_stage(try_dir, "repaired")
    if before is None or after is None:
        return None, before, after
    return after < before, before, after


def _is_true_cex(validation_result: Dict[str, Any], target_error: Optional[str]) -> bool:
    detected = bool(validation_result.get("detected"))
    region = validation_result.get("failure_region")

    if target_error == "InvFailFront":
        return bool(detected and region == "before")
    if target_error == "InvFailEnd":
        return bool(detected and region == "after")

    # Mirror pipeline behavior for other or unknown error types.
    return True


def _phi_coefficient(n11: int, n10: int, n01: int, n00: int) -> float:
    denom = math.sqrt(
        (n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)
    )
    if denom == 0:
        return 0.0
    return (n11 * n00 - n10 * n01) / denom


def collect_cex_validation_stats(
    root: Path | str,
    strategy: str,
    gen_id: str = "gen_0",
    include_steps: bool = False,
    include_all_failed_try_dirs: bool = False,
) -> Dict[str, Any]:
    gen_dirs = find_gen_dirs(root=root, strategy=strategy, gen_id=gen_id)

    scanned_steps = 0
    validation_steps = 0
    validation_steps_with_cex = 0
    error_reducing_steps = 0
    comparable_steps = 0
    comparable_validation_steps = 0
    total_cex = 0
    validated_true_cex = 0
    failed_validation_cex = 0
    all_failed_steps = 0
    steps_missing_target_error = 0
    steps_missing_error_counts = 0

    # Contingency for:
    # X = 1 iff all validation failed
    # Y = 1 iff this step reduced the error count
    n11 = 0
    n10 = 0
    n01 = 0
    n00 = 0

    step_rows: List[Dict[str, Any]] = []
    all_failed_try_dirs: List[str] = []

    for gen_dir in gen_dirs:
        task_id = gen_dir.parent.parent.name
        trajectory_attempts = _load_trajectory_attempts(gen_dir)

        for try_dir in _iter_try_dirs(gen_dir):
            scanned_steps += 1
            errors_decreased, errors_before, errors_after = _error_improvement_for_try(
                try_dir
            )
            if errors_decreased is None:
                steps_missing_error_counts += 1
            else:
                comparable_steps += 1
                if errors_decreased:
                    error_reducing_steps += 1

            batch_results = _read_json_safe(try_dir / "harness_before" / "batch_results.json")
            if not isinstance(batch_results, list):
                if include_steps:
                    step_rows.append(
                        {
                            "task_id": task_id,
                            "try_dir": str(try_dir),
                            "attempt": _try_attempt_number(try_dir),
                            "target_error": _target_error_for_try(
                                try_dir, trajectory_attempts
                            ),
                            "errors_before": errors_before,
                            "errors_after": errors_after,
                            "errors_decreased": errors_decreased,
                            "validation_attempted": False,
                            "total_cex": 0,
                            "validated_true_cex": 0,
                            "failed_validation_cex": 0,
                            "all_cex_validation_failed": False,
                        }
                    )
                continue

            validation_steps += 1

            target_error = _target_error_for_try(try_dir, trajectory_attempts)
            if target_error is None:
                steps_missing_target_error += 1

            total = len(batch_results)
            true_count = 0
            for item in batch_results:
                if isinstance(item, dict) and _is_true_cex(item, target_error):
                    true_count += 1

            failed_count = total - true_count
            all_failed = total > 0 and true_count == 0

            total_cex += total
            validated_true_cex += true_count
            failed_validation_cex += failed_count

            if total > 0:
                validation_steps_with_cex += 1
                if all_failed:
                    all_failed_steps += 1
                    if include_all_failed_try_dirs:
                        all_failed_try_dirs.append(str(try_dir))

                if errors_decreased is not None:
                    comparable_validation_steps += 1
                    if all_failed and errors_decreased:
                        n11 += 1
                    elif all_failed and not errors_decreased:
                        n10 += 1
                    elif (not all_failed) and errors_decreased:
                        n01 += 1
                    else:
                        n00 += 1

            if include_steps:
                step_rows.append(
                    {
                        "task_id": task_id,
                        "try_dir": str(try_dir),
                        "attempt": _try_attempt_number(try_dir),
                        "target_error": target_error,
                        "errors_before": errors_before,
                        "errors_after": errors_after,
                        "errors_decreased": errors_decreased,
                        "validation_attempted": True,
                        "total_cex": total,
                        "validated_true_cex": true_count,
                        "failed_validation_cex": failed_count,
                        "all_cex_validation_failed": all_failed,
                    }
                )

    phi = _phi_coefficient(n11, n10, n01, n00)
    error_reduction_rate_all_failed = n11 / (n11 + n10) if (n11 + n10) else 0.0
    error_reduction_rate_not_all_failed = (
        n01 / (n01 + n00) if (n01 + n00) else 0.0
    )

    stats: Dict[str, Any] = {
        "summary": {
            "root": str(Path(root).resolve()),
            "strategy": strategy,
            "gen_id": gen_id,
            "matched_gen_dirs": len(gen_dirs),
            "scanned_steps": scanned_steps,
            "validation_steps": validation_steps,
            "validation_steps_with_cex": validation_steps_with_cex,
            "comparable_steps": comparable_steps,
            "comparable_validation_steps": comparable_validation_steps,
            "error_reducing_steps": error_reducing_steps,
            "steps_missing_target_error": steps_missing_target_error,
            "steps_missing_error_counts": steps_missing_error_counts,
            "total_cex": total_cex,
            "validated_true_cex": validated_true_cex,
            "failed_validation_cex": failed_validation_cex,
            "failed_validation_cex_proportion": (
                failed_validation_cex / total_cex if total_cex else 0.0
            ),
            "all_failed_steps": all_failed_steps,
            "all_failed_step_proportion_among_validation_steps": (
                all_failed_steps / validation_steps_with_cex
                if validation_steps_with_cex
                else 0.0
            ),
            "all_failed_step_proportion_among_all_steps": (
                all_failed_steps / scanned_steps if scanned_steps else 0.0
            ),
        },
        "correlation": {
            "eligible_steps": comparable_validation_steps,
            "contingency": {
                "all_failed_and_error_reduced": n11,
                "all_failed_and_not_error_reduced": n10,
                "not_all_failed_and_error_reduced": n01,
                "not_all_failed_and_not_error_reduced": n00,
            },
            "phi_coefficient": phi,
            "error_reduction_rate_when_all_failed": error_reduction_rate_all_failed,
            "error_reduction_rate_when_not_all_failed": (
                error_reduction_rate_not_all_failed
            ),
        },
    }

    if include_steps:
        stats["steps"] = step_rows
    if include_all_failed_try_dirs:
        stats["all_failed_try_dirs"] = all_failed_try_dirs

    return stats


def _format_pct(value: float) -> str:
    return f"{value * 100:6.2f}%"


def render_text_report(stats: Dict[str, Any]) -> str:
    summary = stats["summary"]
    corr = stats["correlation"]
    contingency = corr["contingency"]
    all_failed_try_dirs = stats.get("all_failed_try_dirs")

    lines = [
        (
            f"Scanned {summary['matched_gen_dirs']} matching `{summary['strategy']}` / "
            f"`{summary['gen_id']}` directories under {summary['root']}"
        ),
        (
            f"Steps: {summary['scanned_steps']} | "
            f"Validation steps: {summary['validation_steps']} | "
            f"Validation steps with CEXs: {summary['validation_steps_with_cex']} | "
            f"Comparable steps: {summary['comparable_steps']} | "
            f"Error-reducing steps: {summary['error_reducing_steps']}"
        ),
        (
            f"Validated true CEXs: {summary['validated_true_cex']} / {summary['total_cex']} | "
            f"Failed validation CEXs: {summary['failed_validation_cex']} / {summary['total_cex']} "
            f"({_format_pct(summary['failed_validation_cex_proportion'])})"
        ),
        (
            f"Steps with ALL failed CEX validation: {summary['all_failed_steps']} / "
            f"{summary['validation_steps_with_cex']} "
            f"({_format_pct(summary['all_failed_step_proportion_among_validation_steps'])}) "
            f"among validation steps with CEXs"
        ),
        (
            f"Steps with ALL failed CEX validation: {summary['all_failed_steps']} / "
            f"{summary['scanned_steps']} "
            f"({_format_pct(summary['all_failed_step_proportion_among_all_steps'])}) "
            f"among all scanned steps"
        ),
        "",
        "Correlation Between ALL Failed Validation and Error Reduction",
        (
            f"Eligible steps: {corr['eligible_steps']} | "
            f"phi coefficient: {corr['phi_coefficient']:.4f}"
        ),
        (
            f"Error-reduction rate when ALL validation failed: "
            f"{contingency['all_failed_and_error_reduced']} / "
            f"{contingency['all_failed_and_error_reduced'] + contingency['all_failed_and_not_error_reduced']} "
            f"({_format_pct(corr['error_reduction_rate_when_all_failed'])})"
        ),
        (
            f"Error-reduction rate when NOT all validation failed: "
            f"{contingency['not_all_failed_and_error_reduced']} / "
            f"{contingency['not_all_failed_and_error_reduced'] + contingency['not_all_failed_and_not_error_reduced']} "
            f"({_format_pct(corr['error_reduction_rate_when_not_all_failed'])})"
        ),
        (
            "Contingency table "
            f"[all_failed_and_error_reduced={contingency['all_failed_and_error_reduced']}, "
            f"all_failed_and_not_error_reduced={contingency['all_failed_and_not_error_reduced']}, "
            f"not_all_failed_and_error_reduced={contingency['not_all_failed_and_error_reduced']}, "
            f"not_all_failed_and_not_error_reduced={contingency['not_all_failed_and_not_error_reduced']}]"
        ),
    ]

    if summary["steps_missing_target_error"]:
        lines.extend(
            [
                "",
                (
                    f"Warning: {summary['steps_missing_target_error']} validation steps were "
                    "missing a target error label and were evaluated with the pipeline's "
                    "fallback semantics for non-loop-specific errors."
                ),
            ]
        )

    if summary["steps_missing_error_counts"]:
        lines.extend(
            [
                "",
                (
                    f"Warning: {summary['steps_missing_error_counts']} steps were missing "
                    "before/after error counts and were excluded from the error-reduction "
                    "correlation."
                ),
            ]
        )

    if isinstance(all_failed_try_dirs, list):
        lines.extend(
            [
                "",
                (
                    "try_dir paths with ALL failed CEX validation "
                    f"({len(all_failed_try_dirs)}):"
                ),
            ]
        )
        if all_failed_try_dirs:
            lines.extend(all_failed_try_dirs)
        else:
            lines.append("(none)")

    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate CEX validation failure statistics across pipeline runs."
    )
    parser.add_argument(
        "root",
        help=(
            "Root directory to scan. This may be a benchmark/model directory, a single "
            "task directory, a strategy directory, or a gen directory."
        ),
    )
    parser.add_argument(
        "--strategy",
        required=True,
        help="Strategy directory name, e.g. cex_repair_z3_mut_val_10.",
    )
    parser.add_argument(
        "--gen-id",
        default="gen_0",
        help="Generation directory name to scan inside each strategy directory.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--include-steps",
        action="store_true",
        help="Include per-step records in JSON output.",
    )
    parser.add_argument(
        "--print-all-failed-try-dirs",
        action="store_true",
        help=(
            "Include the try_dir paths for steps where every CEX validation failed. "
            "Shown in text output and included in JSON output."
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file path. Defaults to stdout.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    stats = collect_cex_validation_stats(
        root=args.root,
        strategy=args.strategy,
        gen_id=args.gen_id,
        include_steps=args.include_steps,
        include_all_failed_try_dirs=args.print_all_failed_try_dirs,
    )

    if args.format == "json":
        payload = json.dumps(stats, indent=2)
    else:
        payload = render_text_report(stats)

    if args.output:
        Path(args.output).write_text(
            payload + ("\n" if not payload.endswith("\n") else "")
        )
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
