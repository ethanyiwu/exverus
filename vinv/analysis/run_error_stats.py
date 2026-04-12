"""
Aggregate run-level error statistics from pipeline repair trajectories.

Examples:
    uv run python -m vinv.analysis.run_error_stats \
        results/pipeline/gpt-4o/CLEANED_VB \
        --strategy cex_repair_z3_mut_val_10

    uv run python -m vinv.analysis.run_error_stats \
        results/pipeline/gpt-4o/CLEANED_VB/verusbench_diffy_brs1 \
        --strategy cex_repair_z3_mut_val_10
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _repo_root() -> Path:
    # vinv/analysis/run_error_stats.py -> parents:
    # 0: analysis, 1: vinv, 2: repo root
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _repo_root()
VEVAL_PY = REPO_ROOT / "verus-proof-synthesis" / "code" / "veval.py"
COMPILATION_ERROR = "compilation_error"


def _read_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _read_text_safe(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


def _load_veval_message_to_type_name() -> Dict[str, str]:
    """
    Load the message -> VerusErrorType.name mapping from veval.py without importing it.
    """
    if not VEVAL_PY.is_file():
        return {}

    mapping: Dict[str, str] = {}
    in_map = False
    for raw in VEVAL_PY.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not in_map:
            if line.startswith("m2VerusError") and "{" in line:
                in_map = True
            continue

        if line.startswith("}"):
            break

        if not line.startswith('"'):
            continue

        try:
            msg = line.split('"', 2)[1]
        except Exception:
            continue

        marker = "VerusErrorType."
        if marker not in line:
            continue

        tail = line.split(marker, 1)[1]
        type_name = ""
        for ch in tail:
            if ch.isalnum() or ch == "_":
                type_name += ch
            else:
                break

        if msg and type_name:
            mapping[msg] = type_name

    return mapping


_VEVAL_MSG2TYPE: Optional[Dict[str, str]] = None


def _msg_to_type_name(msg: str) -> str:
    global _VEVAL_MSG2TYPE
    if _VEVAL_MSG2TYPE is None:
        _VEVAL_MSG2TYPE = _load_veval_message_to_type_name()
    return _VEVAL_MSG2TYPE.get(msg, msg)


def _canonicalize_error_message(msg: str, block_text: str) -> str:
    canonical = _msg_to_type_name(msg)
    if canonical == "PreCondFail" and "vec.view().len()" in block_text:
        return "PreCondFailVecLen"
    return canonical


def _extract_error_types_from_text(text: str) -> List[str]:
    """
    Parse human-readable Verus logs and return canonical error-type names.

    Duplicates are preserved because a single step can encounter the same
    canonical error multiple times.
    """
    if not text:
        return []

    lines = text.splitlines()
    errors: List[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line.startswith("error:"):
            idx += 1
            continue

        msg = line[len("error:") :].strip()
        start = idx
        idx += 1
        while idx < len(lines) and not lines[idx].strip().startswith("error:"):
            idx += 1

        if not msg or msg.startswith("aborting due to"):
            continue

        block_text = "\n".join(lines[start:idx])
        errors.append(_canonicalize_error_message(msg, block_text))

    return errors


def _normalize_error_list(errors: Iterable[Any]) -> List[str]:
    normalized: List[str] = []
    for error in errors:
        if isinstance(error, str):
            stripped = error.strip()
            if stripped:
                normalized.append(stripped)
    return normalized


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


def _errors_from_trajectory_iteration(iteration: Dict[str, Any]) -> List[str]:
    all_errors = _normalize_error_list(iteration.get("all_errors", []))
    if all_errors:
        return all_errors

    target_error = iteration.get("target_error")
    if isinstance(target_error, str) and target_error.strip():
        return [target_error.strip()]

    status = iteration.get("status")
    if isinstance(status, dict) and status.get("compilation_error") is True:
        return [COMPILATION_ERROR]

    return []


def _errors_from_try_dir(try_dir: Path) -> List[str]:
    input_text = _read_text_safe(try_dir / "input_err.txt")
    if not input_text:
        input_text = _read_text_safe(try_dir / "input_out.txt")

    errors = _extract_error_types_from_text(input_text)
    if errors:
        return errors

    input_status = _read_text_safe(try_dir / "input_verify_status.txt").strip()
    if input_status == COMPILATION_ERROR:
        return [COMPILATION_ERROR]

    repair_status = _read_json_safe(try_dir / "repair_status.json")
    if repair_status:
        error_type = repair_status.get("error_type")
        if isinstance(error_type, str) and error_type.strip():
            return [error_type.strip()]

    return []


def _collect_attempt_errors(gen_dir: Path) -> Dict[int, List[str]]:
    attempts: Dict[int, List[str]] = {}

    trajectory = _read_json_safe(gen_dir / "trajectory.json")
    if trajectory:
        for iteration in trajectory.get("iterations", []):
            if not isinstance(iteration, dict):
                continue
            attempt = iteration.get("attempt")
            if not isinstance(attempt, int):
                continue
            attempts[attempt] = _errors_from_trajectory_iteration(iteration)

    for try_dir in _iter_try_dirs(gen_dir):
        attempt = _try_attempt_number(try_dir)
        if attempt is None:
            continue
        if attempts.get(attempt):
            continue
        fallback_errors = _errors_from_try_dir(try_dir)
        if fallback_errors:
            attempts[attempt] = fallback_errors
        elif attempt not in attempts:
            attempts[attempt] = []

    return dict(sorted(attempts.items()))


def find_gen_dirs(root: Path | str, strategy: str, gen_id: str = "gen_0") -> List[Path]:
    root_path = Path(root).resolve()
    candidates = set()

    if root_path.is_dir():
        if root_path.name == gen_id and root_path.parent.name == strategy:
            candidates.add(root_path)

        strategy_dir = root_path / strategy
        if strategy_dir.is_dir():
            gen_dir = strategy_dir / gen_id
            if gen_dir.is_dir():
                candidates.add(gen_dir.resolve())

        if root_path.name == strategy:
            gen_dir = root_path / gen_id
            if gen_dir.is_dir():
                candidates.add(gen_dir.resolve())

        for path in root_path.rglob(gen_id):
            if path.is_dir() and path.parent.name == strategy:
                candidates.add(path.resolve())

    return sorted(candidates)


def collect_run_error_stats(
    root: Path | str,
    strategy: str,
    gen_id: str = "gen_0",
) -> Dict[str, Any]:
    gen_dirs = find_gen_dirs(root=root, strategy=strategy, gen_id=gen_id)

    occurrence_counter: Counter[str] = Counter()
    step_counter: Counter[str] = Counter()
    task_counter: Counter[str] = Counter()

    total_steps = 0
    total_occurrences = 0
    total_non_compilation_steps = 0
    total_non_compilation_occurrences = 0
    steps_missing_errors = 0
    tasks_with_steps = 0

    for gen_dir in gen_dirs:
        attempt_errors = _collect_attempt_errors(gen_dir)
        if not attempt_errors:
            continue

        tasks_with_steps += 1
        task_seen_errors = set()

        for _, errors in attempt_errors.items():
            total_steps += 1
            if not errors:
                total_non_compilation_steps += 1
                steps_missing_errors += 1
                continue

            total_occurrences += len(errors)
            occurrence_counter.update(errors)
            total_non_compilation_occurrences += sum(
                1 for error in errors if error != COMPILATION_ERROR
            )

            unique_step_errors = set(errors)
            step_counter.update(unique_step_errors)
            task_seen_errors.update(unique_step_errors)
            if COMPILATION_ERROR not in unique_step_errors:
                total_non_compilation_steps += 1

        for error in task_seen_errors:
            task_counter[error] += 1

    rows = []
    all_errors = set(occurrence_counter) | set(step_counter) | set(task_counter)
    for error in sorted(all_errors):
        occurrence_count = occurrence_counter[error]
        step_count = step_counter[error]
        task_count = task_counter[error]
        rows.append(
            {
                "error": error,
                "occurrence_count": occurrence_count,
                "occurrence_proportion": (
                    occurrence_count / total_occurrences if total_occurrences else 0.0
                ),
                "occurrence_non_compilation_proportion": (
                    occurrence_count / total_non_compilation_occurrences
                    if error != COMPILATION_ERROR and total_non_compilation_occurrences
                    else None
                ),
                "step_count": step_count,
                "step_proportion": step_count / total_steps if total_steps else 0.0,
                "step_non_compilation_proportion": (
                    step_count / total_non_compilation_steps
                    if error != COMPILATION_ERROR and total_non_compilation_steps
                    else None
                ),
                "task_count": task_count,
                "task_proportion": (
                    task_count / tasks_with_steps if tasks_with_steps else 0.0
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            -row["occurrence_count"],
            -row["step_count"],
            -row["task_count"],
            row["error"],
        )
    )

    return {
        "summary": {
            "root": str(Path(root).resolve()),
            "strategy": strategy,
            "gen_id": gen_id,
            "matched_gen_dirs": len(gen_dirs),
            "tasks_with_steps": tasks_with_steps,
            "total_steps": total_steps,
            "total_non_compilation_steps": total_non_compilation_steps,
            "steps_missing_errors": steps_missing_errors,
            "total_error_occurrences": total_occurrences,
            "total_non_compilation_error_occurrences": total_non_compilation_occurrences,
        },
        "rows": rows,
    }


def _format_pct(value: float) -> str:
    return f"{value * 100:6.2f}%"


def _format_optional_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return _format_pct(value)


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def render_text_report(stats: Dict[str, Any], top: Optional[int] = None) -> str:
    summary = stats["summary"]
    rows = stats["rows"][:top] if top else stats["rows"]

    header = [
        (
            f"Scanned {summary['matched_gen_dirs']} matching `{summary['strategy']}` / "
            f"`{summary['gen_id']}` directories under {summary['root']}"
        ),
        (
            f"Tasks with steps: {summary['tasks_with_steps']} | "
            f"Total steps: {summary['total_steps']} | "
            f"Non-compilation steps: {summary['total_non_compilation_steps']} | "
            f"Steps missing errors: {summary['steps_missing_errors']} | "
            f"Total error occurrences: {summary['total_error_occurrences']}"
        ),
        (
            "Non-compilation error occurrences: "
            f"{summary['total_non_compilation_error_occurrences']}"
        ),
        "",
    ]

    if not rows:
        header.append("No errors found.")
        return "\n".join(header)

    table_header = (
        f"{'error':<22} {'occurrences':>12} {'occ%':>8} {'occ%_nc':>8} "
        f"{'steps':>8} {'step%':>8} {'step%_nc':>9} {'tasks':>8} {'task%':>8}"
    )
    lines = header + [table_header, "-" * len(table_header)]
    for row in rows:
        lines.append(
            f"{row['error']:<22} "
            f"{row['occurrence_count']:>12} "
            f"{_format_pct(row['occurrence_proportion']):>8} "
            f"{_format_optional_pct(row['occurrence_non_compilation_proportion']):>8} "
            f"{row['step_count']:>8} "
            f"{_format_pct(row['step_proportion']):>8} "
            f"{_format_optional_pct(row['step_non_compilation_proportion']):>9} "
            f"{row['task_count']:>8} "
            f"{_format_pct(row['task_proportion']):>8}"
        )

    return "\n".join(lines)


def render_markdown_report(stats: Dict[str, Any], top: Optional[int] = None) -> str:
    summary = stats["summary"]
    rows = stats["rows"][:top] if top else stats["rows"]

    lines = [
        (
            f"Scanned {summary['matched_gen_dirs']} matching `{summary['strategy']}` / "
            f"`{summary['gen_id']}` directories under `{summary['root']}`"
        ),
        "",
        (
            f"Tasks with steps: {summary['tasks_with_steps']} | "
            f"Total steps: {summary['total_steps']} | "
            f"Non-compilation steps: {summary['total_non_compilation_steps']} | "
            f"Steps missing errors: {summary['steps_missing_errors']}"
        ),
        (
            "Total error occurrences: "
            f"{summary['total_error_occurrences']} | "
            "Non-compilation error occurrences: "
            f"{summary['total_non_compilation_error_occurrences']}"
        ),
        "",
    ]

    if not rows:
        lines.append("No errors found.")
        return "\n".join(lines)

    headers = [
        "error",
        "occurrences",
        "occ%",
        "occ%_nc",
        "steps",
        "step%",
        "step%_nc",
        "tasks",
        "task%",
    ]
    aligns = ["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]
    lines.extend(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(aligns) + " |",
        ]
    )

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_markdown_cell(row["error"]),
                    str(row["occurrence_count"]),
                    _format_pct(row["occurrence_proportion"]),
                    _format_optional_pct(row["occurrence_non_compilation_proportion"]),
                    str(row["step_count"]),
                    _format_pct(row["step_proportion"]),
                    _format_optional_pct(row["step_non_compilation_proportion"]),
                    str(row["task_count"]),
                    _format_pct(row["task_proportion"]),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate per-error statistics across pipeline runs."
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
        "--top",
        type=int,
        default=None,
        help="Only print the top N errors after sorting by occurrence count.",
    )
    parser.add_argument(
        "--markdown-table",
        action="store_true",
        help="Render text output as a Markdown table.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file path. Defaults to stdout.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    stats = collect_run_error_stats(
        root=args.root,
        strategy=args.strategy,
        gen_id=args.gen_id,
    )

    if args.format == "json":
        if args.markdown_table:
            parser.error("--markdown-table can only be used with --format text")
        payload = json.dumps(stats, indent=2)
    elif args.markdown_table:
        payload = render_markdown_report(stats, top=args.top)
    else:
        payload = render_text_report(stats, top=args.top)

    if args.output:
        Path(args.output).write_text(payload + ("\n" if not payload.endswith("\n") else ""))
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
