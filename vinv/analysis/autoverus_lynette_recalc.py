from __future__ import annotations

import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

SPECIAL_WORDS = ("assume(", "admit()")
SCORE_RE = re.compile(r"[Ss]core:\s*\((\d+),\s*(\d+)\)")
VERIFIED_RE = re.compile(
    r"Compilation Error:\s*False,\s*Verified:\s*(-?\d+),\s*Errors:\s*(\d+)"
)
SAFETY_MARKERS = (
    "Safe: True",
    "Safe: False",
    "Safe: None",
    "is safe: True",
    "is safe: False",
    "is safe: None",
)


@dataclass(frozen=True)
class Attempt:
    task_id: str
    benchmark: str
    attempt: int
    input_file: Path
    output_file: Path
    summary_verified: bool


@dataclass(frozen=True)
class Safety:
    status: str
    returncode: int
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_lynette_bin() -> Path:
    if os.environ.get("LYNETTE_PATH"):
        return Path(str(os.environ["LYNETTE_PATH"]))
    return (
        repo_root()
        / "verus-proof-synthesis"
        / "utils"
        / "lynette"
        / "source"
        / "target"
        / "debug"
        / "lynette"
    )


def read_summary(run_dir: Path) -> dict[str, Any]:
    return json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))


def load_attempts(summary: dict[str, Any]) -> list[Attempt]:
    attempts = []
    for task in summary["results"]:
        for attempt in task["attempts"]:
            attempts.append(
                Attempt(
                    task_id=str(task["task_id"]),
                    benchmark=str(task["benchmark"]),
                    attempt=int(attempt["attempt"]),
                    input_file=Path(str(task["input_file"])),
                    output_file=Path(str(attempt["output_file"])),
                    summary_verified=bool(attempt["verified"]),
                )
            )
    return attempts


def marker(text: str) -> str:
    return next((item for item in SAFETY_MARKERS if item in text), "none")


def has_special_word(path: Path, text: str) -> bool:
    return "havoc_inline_post" not in path.name and any(
        word in text for word in SPECIAL_WORDS
    )


def verus_verified(text: str) -> bool:
    return any(
        int(verified) > 0 and int(errors) == 0
        for verified, errors in SCORE_RE.findall(text)
    ) or any(
        int(verified) > 0 and int(errors) == 0
        for verified, errors in VERIFIED_RE.findall(text)
    )


def safety_check(lynette_bin: Path, original: Path, candidate: Path) -> Safety:
    result = subprocess.run(
        [str(lynette_bin), "compare", "-t", str(original), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    )
    message = (result.stdout or result.stderr).strip()
    if result.returncode == 0:
        return Safety("safe", result.returncode, message)
    if result.returncode == 1:
        return Safety("different", result.returncode, message)
    return Safety("error", result.returncode, message)


def summarize(
    summary: dict[str, Any],
    attempts: list[Attempt],
    verified_attempts: set[tuple[str, int]],
) -> dict[str, Any]:
    tasks = summary["results"]
    solved_tasks = {task_id for task_id, _ in verified_attempts}
    pass1_tasks = {task_id for task_id, attempt in verified_attempts if attempt == 1}
    by_benchmark: dict[str, dict[str, Any]] = {}
    for task in tasks:
        benchmark = str(task["benchmark"])
        info = by_benchmark.setdefault(
            benchmark,
            {
                "tasks": 0,
                "attempts": 0,
                "verified_attempts": 0,
                "solved": 0,
                "pass@1_solved": 0,
            },
        )
        info["tasks"] += 1
        info["solved"] += int(str(task["task_id"]) in solved_tasks)
        info["pass@1_solved"] += int(str(task["task_id"]) in pass1_tasks)
    for attempt in attempts:
        info = by_benchmark[attempt.benchmark]
        info["attempts"] += 1
        info["verified_attempts"] += int(
            (attempt.task_id, attempt.attempt) in verified_attempts
        )
    attempts_per_task = int(summary["attempts_per_task"])
    for info in by_benchmark.values():
        info["pass@1"] = info["pass@1_solved"] / info["tasks"] if info["tasks"] else 0.0
        info[f"pass@{attempts_per_task}"] = (
            info["solved"] / info["tasks"] if info["tasks"] else 0.0
        )
    return {
        "tasks": len(tasks),
        "attempts": len(attempts),
        "verified_attempts": len(verified_attempts),
        "pass@1_solved_tasks": len(pass1_tasks),
        "pass@1": len(pass1_tasks) / len(tasks) if tasks else 0.0,
        "solved_tasks": len(solved_tasks),
        f"pass@{attempts_per_task}": len(solved_tasks) / len(tasks) if tasks else 0.0,
        "by_benchmark": by_benchmark,
    }


def original_stats(summary: dict[str, Any], attempts: list[Attempt]) -> dict[str, Any]:
    return summarize(
        summary,
        attempts,
        original_verified_attempts(attempts),
    )


def original_verified_attempts(attempts: list[Attempt]) -> set[tuple[str, int]]:
    return {
        (attempt.task_id, attempt.attempt)
        for attempt in attempts
        if attempt.summary_verified
    }


def delta_stats(
    left: set[tuple[str, int]], right: set[tuple[str, int]]
) -> dict[str, int]:
    return {
        "attempts": len(left - right),
        "tasks": len(
            {task_id for task_id, _ in left} - {task_id for task_id, _ in right}
        ),
    }


def task_dir(attempt: Attempt) -> Path:
    return attempt.output_file.parent


def repair_candidates(attempt: Attempt) -> list[Path]:
    repair_dir = task_dir(attempt) / f"intermediate-{attempt.attempt}" / "repair"
    return sorted(repair_dir.glob("repair-*.rs")) if repair_dir.is_dir() else []


def compare_record(
    attempt: Attempt,
    path: Path,
    safety: Safety,
    kind: str,
) -> dict[str, Any]:
    return {
        "task_id": attempt.task_id,
        "benchmark": attempt.benchmark,
        "attempt": attempt.attempt,
        "kind": kind,
        "path": str(path),
        "safety": safety.status,
        "returncode": safety.returncode,
        "message": safety.message.splitlines()[:3],
    }


def collect_recalculated_stats(
    run_dir: Path,
    lynette_bin: Path | None = None,
    include_repairs: bool = True,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    lynette_bin = (lynette_bin or default_lynette_bin()).resolve()
    if not lynette_bin.is_file():
        raise FileNotFoundError(f"Lynette binary not found: {lynette_bin}")

    summary = read_summary(run_dir)
    attempts = load_attempts(summary)
    final_verified: set[tuple[str, int]] = set()
    rescued_verified: set[tuple[str, int]] = set()
    compare_counts: dict[str, Counter[str]] = {"final": Counter(), "repair": Counter()}
    marker_counts: dict[str, Counter[str]] = {"final": Counter(), "repair": Counter()}
    final_records = []
    repair_records = []

    for attempt in attempts:
        text = (
            attempt.output_file.read_text(errors="replace")
            if attempt.output_file.is_file()
            else ""
        )
        marker_counts["final"][marker(text)] += 1
        if (
            not attempt.output_file.is_file()
            or not verus_verified(text)
            or has_special_word(attempt.output_file, text)
        ):
            compare_counts["final"]["not_checked"] += 1
            continue
        safety = safety_check(lynette_bin, attempt.input_file, attempt.output_file)
        compare_counts["final"][safety.status] += 1
        final_records.append(
            compare_record(attempt, attempt.output_file, safety, "final")
        )
        if safety.status == "safe":
            final_verified.add((attempt.task_id, attempt.attempt))

    if include_repairs:
        for attempt in attempts:
            for candidate in repair_candidates(attempt):
                text = candidate.read_text(errors="replace")
                marker_counts["repair"][marker(text)] += 1
                if not verus_verified(text) or has_special_word(candidate, text):
                    compare_counts["repair"]["not_checked"] += 1
                    continue
                safety = safety_check(lynette_bin, attempt.input_file, candidate)
                compare_counts["repair"][safety.status] += 1
                record = compare_record(attempt, candidate, safety, "repair")
                repair_records.append(record)
                if (
                    safety.status == "safe"
                    and (attempt.task_id, attempt.attempt) not in final_verified
                ):
                    rescued_verified.add((attempt.task_id, attempt.attempt))

    original_verified = original_verified_attempts(attempts)
    with_repairs = final_verified | rescued_verified
    return {
        "run_dir": str(run_dir),
        "lynette_bin": str(lynette_bin),
        "summary_json": str(run_dir / "summary.json"),
        "original": summarize(summary, attempts, original_verified),
        "strict_final": summarize(summary, attempts, final_verified),
        "with_safe_repairs": summarize(summary, attempts, with_repairs),
        "rescued": {
            "attempts": len(rescued_verified),
            "tasks": len({task_id for task_id, _ in rescued_verified}),
        },
        "deltas": {
            "strict_final_lost_from_original": delta_stats(
                original_verified, final_verified
            ),
            "with_safe_repairs_new_over_original": delta_stats(
                with_repairs, original_verified
            ),
            "with_safe_repairs_missing_from_original": delta_stats(
                original_verified, with_repairs
            ),
        },
        "compare_counts": {key: dict(value) for key, value in compare_counts.items()},
        "marker_counts": {key: dict(value) for key, value in marker_counts.items()},
        "final_records": final_records,
        "repair_records": repair_records,
    }


def render_text(report: dict[str, Any], examples: int = 12) -> str:
    attempts = int(report["original"]["attempts"])
    tasks = int(report["original"]["tasks"])
    attempts_per_task = attempts // tasks if tasks else 0
    pass_key = f"pass@{attempts_per_task}"
    lines = [
        f"Run: {report['run_dir']}",
        f"Lynette: {report['lynette_bin']}",
        "",
        "Overall:",
    ]
    for name in ("original", "strict_final", "with_safe_repairs"):
        stats = report[name]
        lines.append(
            f"- {name}: pass@1 {stats['pass@1']:.3f} "
            f"({stats['pass@1_solved_tasks']}/{stats['tasks']} tasks), "
            f"{pass_key} {stats[pass_key]:.3f} "
            f"({stats['solved_tasks']}/{stats['tasks']} tasks), "
            f"verified attempts {stats['verified_attempts']}/{stats['attempts']}"
        )
    lines += [
        f"- rescued: attempts {report['rescued']['attempts']}, tasks {report['rescued']['tasks']}",
        f"- strict final lost from original: attempts {report['deltas']['strict_final_lost_from_original']['attempts']}, "
        f"tasks {report['deltas']['strict_final_lost_from_original']['tasks']}",
        f"- with repairs new over original: attempts {report['deltas']['with_safe_repairs_new_over_original']['attempts']}, "
        f"tasks {report['deltas']['with_safe_repairs_new_over_original']['tasks']}",
        f"- with repairs missing from original: attempts {report['deltas']['with_safe_repairs_missing_from_original']['attempts']}, "
        f"tasks {report['deltas']['with_safe_repairs_missing_from_original']['tasks']}",
        "",
        "Lynette comparison counts:",
        f"- final: {report['compare_counts']['final']}",
        f"- repair: {report['compare_counts']['repair']}",
        "",
        "By benchmark with safe repairs:",
    ]
    for benchmark, stats in sorted(report["with_safe_repairs"]["by_benchmark"].items()):
        lines.append(
            f"- {benchmark}: pass@1 {stats['pass@1']:.3f}, "
            f"{pass_key} {stats['solved']}/{stats['tasks']} ({stats[pass_key]:.3f})"
        )
    safe_repairs = [
        record for record in report["repair_records"] if record["safety"] == "safe"
    ]
    if safe_repairs:
        lines += ["", "Safe repair examples:"]
        for record in safe_repairs[:examples]:
            lines.append(
                f"- {record['task_id']} attempt {record['attempt']}: {record['path']}"
            )
    return "\n".join(lines)


def main(
    run_dir: Path = typer.Argument(
        ..., exists=True, file_okay=False, help="AutoVerus run directory."
    ),
    lynette_bin: Path | None = typer.Option(
        None,
        "--lynette-bin",
        exists=True,
        dir_okay=False,
        help="Working Lynette binary.",
    ),
    output: Path | None = typer.Option(None, "--output", help="Write JSON report."),
    format_json: bool = typer.Option(
        False, "--json", help="Print JSON instead of text."
    ),
    include_repairs: bool = typer.Option(
        True, "--repairs/--no-repairs", help="Include verified repair candidates."
    ),
    examples: int = typer.Option(
        12, min=0, help="Number of safe repair examples in text output."
    ),
) -> None:
    report = collect_recalculated_stats(run_dir, lynette_bin, include_repairs)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    typer.echo(
        json.dumps(report, indent=2) if format_json else render_text(report, examples)
    )


if __name__ == "__main__":
    typer.run(main)
