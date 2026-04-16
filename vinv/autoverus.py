from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from vinv.config import (
    ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    AUTOVERUS_TOOL_DIR,
    CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    RESULTS_ROOT_DIR,
    THREEBENCH_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    get_autoverus_config_file,
)

AUTOVERUS_RUNS_DIR = RESULTS_ROOT_DIR / "autoverus_runs"
SPECIAL_WORDS = ("assume(", "admit()")
AUTOVERUS_BENCHMARK_SOURCES = {
    "vb": VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    "cleaned_vb": CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    "additional": ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    "threebench": THREEBENCH_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    "vsbherb": VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
}


@dataclass(frozen=True)
class AutoVerusConfig:
    input_dirs: dict[str, Path]
    output_dir: Path
    tool_dir: Path
    config_file: Path
    temp: float = 1.0
    phase1_examples: tuple[str, ...] = ("3", "6", "7")
    repair_num: int = 10
    disable_safe: bool = False
    repair_uniform: bool = False
    phase_uniform: bool = False
    disable_ranking: bool = False
    direct_repair: bool = False
    disable_one_refinement: int = -1
    is_baseline: bool = False
    num_workers: int = 1
    rerun: bool = False


def parse_phase1_examples(raw: str) -> tuple[str, ...]:
    phase1_examples = tuple(part for part in re.split(r"[\s,]+", raw.strip()) if part)
    if not phase1_examples:
        raise ValueError("Phase-1 examples cannot be empty.")
    return phase1_examples


def resolve_autoverus_input_dirs(
    source: str,
    suite_root: Path | None = None,
) -> dict[str, Path]:
    if suite_root is not None:
        input_dirs = {
            path.name: path for path in sorted(suite_root.iterdir()) if path.is_dir()
        }
        if not input_dirs:
            raise ValueError(f"No benchmark directories found in {suite_root}")
        return input_dirs
    try:
        benchmarks = AUTOVERUS_BENCHMARK_SOURCES[source]
    except KeyError as exc:
        raise ValueError(
            f"Unknown AutoVerus source {source!r}. Choose from {sorted(AUTOVERUS_BENCHMARK_SOURCES)}."
        ) from exc
    return {benchmark: benchmarks[benchmark] for benchmark in sorted(benchmarks)}


def resolve_autoverus_config_file(
    model: str,
    config_file: Path | None = None,
) -> Path:
    return config_file if config_file is not None else get_autoverus_config_file(model)


def build_autoverus_output_dir(
    output_root: Path,
    name: str,
    temp: float,
    stamp: str | None = None,
) -> Path:
    return output_root / f"{stamp or datetime.now().strftime('%Y%m%d')}-{name}-{temp}"


def is_correct_autoverus_output(output_file: Path) -> bool:
    text = output_file.read_text(encoding="utf-8")
    if "safe: false" in text.lower():
        return False
    if "havoc_inline_post" not in output_file.name and any(
        word in text for word in SPECIAL_WORDS
    ):
        return False
    score = re.search(r"[Ss]core: \((\d+), (\d+)\)", text)
    return bool(score and int(score.group(1)) > 0 and int(score.group(2)) == 0)


def build_autoverus_runtime_config(
    tool_dir: Path,
    config_file: Path,
) -> dict[str, object]:
    payload = json.loads(config_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"AutoVerus config must be a JSON object: {config_file}")
    verus_path = (
        os.environ.get("VERUS_PATH")
        or shutil.which("verus")
        or str(payload.get("verus_path") or "")
    )
    if not verus_path:
        raise EnvironmentError(
            "Verus executable not found. Set VERUS_PATH or add `verus` to PATH."
        )
    payload["verus_path"] = verus_path
    payload["example_path"] = str(tool_dir / "code" / "examples")
    payload["lemma_path"] = str(tool_dir / "code" / "lemmas")
    payload["util_path"] = str(tool_dir / "utils")
    return payload


def _build_command(
    config: AutoVerusConfig,
    runtime_config: Path,
    input_file: Path,
    output_file: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(config.tool_dir / "code" / "main.py"),
        "--temp",
        str(config.temp),
        "--mode",
        "gen",
        "--config",
        str(runtime_config),
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--repair",
        str(config.repair_num),
        "--phase1-examples",
        *config.phase1_examples,
        "--disable-one-refinement",
        str(config.disable_one_refinement),
    ]
    if config.disable_safe:
        command.append("--disable-safe")
    if config.repair_uniform:
        command.append("--repair-uniform")
    if config.phase_uniform:
        command.append("--phase-uniform")
    if config.disable_ranking:
        command.append("--disable-ranking")
    if config.direct_repair:
        command.append("--direct-repair")
    if config.is_baseline:
        command.append("--is-baseline")
    return command


def _run_job(job: tuple[list[str], Path, Path, Path]) -> tuple[int, bool]:
    command, scratch_dir, log_file, output_file = job
    scratch_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command,
        cwd=scratch_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        check=False,
    )
    log_file.write_text(completed.stdout or "", encoding="utf-8")
    return completed.returncode, output_file.is_file() and is_correct_autoverus_output(
        output_file
    )


def _run_jobs(
    jobs: list[tuple[list[str], Path, Path, Path]],
    num_workers: int,
) -> list[tuple[int, bool]]:
    if num_workers <= 1:
        return [_run_job(job) for job in jobs]
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        return list(executor.map(_run_job, jobs))


def _run_benchmark(
    config: AutoVerusConfig,
    runtime_config: Path,
    benchmark: str,
    input_dir: Path,
) -> dict[str, int]:
    benchmark_dir = config.output_dir / benchmark
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "total_files": 0,
        "scheduled": 0,
        "existing_verified": 0,
        "existing_unverified": 0,
        "new_verified": 0,
        "new_unverified": 0,
        "failed_runs": 0,
    }
    jobs: list[tuple[list[str], Path, Path, Path]] = []
    for input_file in sorted(path for path in input_dir.iterdir() if path.is_file()):
        summary["total_files"] += 1
        output_file = benchmark_dir / f"1-{input_file.name}"
        log_file = output_file.with_suffix(".log")
        if output_file.exists() and not config.rerun:
            if is_correct_autoverus_output(output_file):
                summary["existing_verified"] += 1
            else:
                summary["existing_unverified"] += 1
            continue
        if config.rerun:
            output_file.unlink(missing_ok=True)
            log_file.unlink(missing_ok=True)
        jobs.append(
            (
                _build_command(config, runtime_config, input_file, output_file),
                benchmark_dir / "_work" / f"1-{input_file.stem}",
                log_file,
                output_file,
            )
        )
    summary["scheduled"] = len(jobs)
    for returncode, verified in _run_jobs(jobs, config.num_workers):
        summary["failed_runs"] += int(returncode != 0)
        key = "new_verified" if verified else "new_unverified"
        summary[key] += 1
    return summary


def run_autoverus(config: AutoVerusConfig) -> dict[str, object]:
    if not (config.tool_dir / "code" / "main.py").is_file():
        raise FileNotFoundError(
            f"AutoVerus entrypoint not found: {config.tool_dir / 'code' / 'main.py'}"
        )
    config.output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="autoverus-config-") as runtime_dir:
        runtime_config = Path(runtime_dir) / "autoverus.runtime.json"
        runtime_config.write_text(
            json.dumps(
                build_autoverus_runtime_config(
                    tool_dir=config.tool_dir,
                    config_file=config.config_file,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        benchmarks = {
            benchmark: _run_benchmark(config, runtime_config, benchmark, input_dir)
            for benchmark, input_dir in sorted(config.input_dirs.items())
        }
    return {"output_dir": config.output_dir, "benchmarks": benchmarks}


def render_autoverus_summary(summary: dict[str, object]) -> str:
    benchmarks = summary["benchmarks"]
    total = lambda key: sum(info[key] for info in benchmarks.values())
    lines = [
        f"Run directory: {summary['output_dir']}",
        f"Benchmarks: {len(benchmarks)}",
        f"Files scanned: {total('total_files')}",
        f"Scheduled: {total('scheduled')}",
        f"Verified: {total('existing_verified') + total('new_verified')} "
        f"(existing {total('existing_verified')}, new {total('new_verified')})",
        f"Existing unverified skipped: {total('existing_unverified')}",
        f"New unverified: {total('new_unverified')}",
        f"Failed subprocesses: {total('failed_runs')}",
    ]
    for benchmark, info in sorted(benchmarks.items()):
        lines.append(
            f"- {benchmark}: {info['existing_verified'] + info['new_verified']}/{info['total_files']} verified"
        )
    return "\n".join(lines)


__all__ = [
    "AUTOVERUS_BENCHMARK_SOURCES",
    "AUTOVERUS_RUNS_DIR",
    "AUTOVERUS_TOOL_DIR",
    "AutoVerusConfig",
    "build_autoverus_output_dir",
    "build_autoverus_runtime_config",
    "is_correct_autoverus_output",
    "parse_phase1_examples",
    "render_autoverus_summary",
    "resolve_autoverus_config_file",
    "resolve_autoverus_input_dirs",
    "run_autoverus",
]
