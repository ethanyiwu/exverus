from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
class AutoVerusRunConfig:
    name: str
    source: str
    benchmark: str
    input_dir: Path
    output_dir: Path
    tool_dir: Path
    config_file: Path
    temp: float
    phase1_examples: tuple[str, ...]
    repair_num: int
    disable_safe: bool = False
    repair_uniform: bool = False
    phase_uniform: bool = False
    disable_ranking: bool = False
    direct_repair: bool = False
    disable_one_refinement: int = -1
    is_baseline: bool = False
    num_workers: int = 1
    rerun: bool = False


@dataclass(frozen=True)
class AutoVerusTask:
    file_name: str
    input_file: Path
    output_file: Path
    log_file: Path
    scratch_dir: Path
    command: list[str]


@dataclass(frozen=True)
class AutoVerusTaskResult:
    file_name: str
    returncode: int
    verified: bool
    elapsed_seconds: float


@dataclass(frozen=True)
class AutoVerusRunSummary:
    output_dir: Path
    total_files: int
    scheduled: int
    existing_verified: int
    existing_unverified: int
    new_verified: int
    new_unverified: int
    failed_runs: int

    @property
    def verified_total(self) -> int:
        return self.existing_verified + self.new_verified


def available_autoverus_benchmarks(source: str) -> tuple[str, ...]:
    benchmarks = AUTOVERUS_BENCHMARK_SOURCES.get(source)
    if benchmarks is None:
        raise ValueError(
            f"Unknown AutoVerus source {source!r}. Choose from {sorted(AUTOVERUS_BENCHMARK_SOURCES)}."
        )
    return tuple(sorted(benchmarks))


def parse_phase1_examples(raw: str) -> tuple[str, ...]:
    phase1_examples = tuple(part for part in re.split(r"[\s,]+", raw.strip()) if part)
    if not phase1_examples:
        raise ValueError("Phase-1 examples cannot be empty.")
    return phase1_examples


def resolve_autoverus_input_dir(
    source: str,
    benchmark: str,
    input_dir: Path | None = None,
) -> Path:
    if input_dir is not None:
        return input_dir
    benchmarks = AUTOVERUS_BENCHMARK_SOURCES.get(source)
    if benchmarks is None:
        raise ValueError(
            f"Unknown AutoVerus source {source!r}. Choose from {sorted(AUTOVERUS_BENCHMARK_SOURCES)}."
        )
    try:
        return benchmarks[benchmark]
    except KeyError as exc:
        raise ValueError(
            f"Unknown benchmark {benchmark!r} for source {source!r}. "
            f"Choose from {sorted(benchmarks)}."
        ) from exc


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
    date_prefix = stamp or datetime.now().strftime("%Y%m%d")
    return output_root / f"{date_prefix}-{name}-{temp}"


def is_correct_autoverus_output(code_file_path: Path) -> bool:
    text = code_file_path.read_text(encoding="utf-8")
    if "safe: false" in text.lower():
        return False
    if "havoc_inline_post" not in code_file_path.name and any(
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


def _write_runtime_config(
    runtime_dir: Path,
    tool_dir: Path,
    config_file: Path,
) -> Path:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    runtime_config = runtime_dir / "autoverus.runtime.json"
    runtime_config.write_text(
        json.dumps(
            build_autoverus_runtime_config(tool_dir=tool_dir, config_file=config_file),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_config


def _build_task(
    config: AutoVerusRunConfig,
    runtime_config: Path,
    input_file: Path,
) -> AutoVerusTask:
    output_file = config.output_dir / f"1-{input_file.name}"
    log_file = output_file.with_suffix(".log")
    scratch_dir = config.output_dir / "_work" / f"1-{input_file.stem}"
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
    return AutoVerusTask(
        file_name=input_file.name,
        input_file=input_file,
        output_file=output_file,
        log_file=log_file,
        scratch_dir=scratch_dir,
        command=command,
    )


def _run_task(task: AutoVerusTask) -> AutoVerusTaskResult:
    task.scratch_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    completed = subprocess.run(
        task.command,
        cwd=task.scratch_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        check=False,
    )
    task.log_file.write_text(completed.stdout or "", encoding="utf-8")
    return AutoVerusTaskResult(
        file_name=task.file_name,
        returncode=completed.returncode,
        verified=task.output_file.is_file() and is_correct_autoverus_output(task.output_file),
        elapsed_seconds=time.perf_counter() - started,
    )


def _run_tasks(
    tasks: list[AutoVerusTask],
    num_workers: int,
) -> list[AutoVerusTaskResult]:
    if num_workers <= 1:
        return [_run_task(task) for task in tasks]
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(_run_task, task) for task in tasks]
        return [future.result() for future in as_completed(futures)]


def render_autoverus_summary(summary: AutoVerusRunSummary) -> str:
    lines = [
        f"Run directory: {summary.output_dir}",
        f"Files scanned: {summary.total_files}",
        f"Scheduled: {summary.scheduled}",
        f"Verified: {summary.verified_total} "
        f"(existing {summary.existing_verified}, new {summary.new_verified})",
        f"Existing unverified skipped: {summary.existing_unverified}",
        f"New unverified: {summary.new_unverified}",
        f"Failed subprocesses: {summary.failed_runs}",
    ]
    return "\n".join(lines)


def run_autoverus(config: AutoVerusRunConfig) -> AutoVerusRunSummary:
    if not (config.tool_dir / "code" / "main.py").is_file():
        raise FileNotFoundError(
            f"AutoVerus entrypoint not found: {config.tool_dir / 'code' / 'main.py'}"
        )
    config.output_dir.mkdir(parents=True, exist_ok=True)
    input_files = sorted(path for path in config.input_dir.iterdir() if path.is_file())
    existing_verified = 0
    existing_unverified = 0
    tasks: list[AutoVerusTask] = []
    with TemporaryDirectory(prefix="autoverus-config-") as runtime_dir_name:
        runtime_config = _write_runtime_config(
            runtime_dir=Path(runtime_dir_name),
            tool_dir=config.tool_dir,
            config_file=config.config_file,
        )
        for input_file in input_files:
            task = _build_task(config=config, runtime_config=runtime_config, input_file=input_file)
            if task.output_file.exists() and not config.rerun:
                if is_correct_autoverus_output(task.output_file):
                    existing_verified += 1
                else:
                    existing_unverified += 1
                continue
            if config.rerun:
                task.output_file.unlink(missing_ok=True)
                task.log_file.unlink(missing_ok=True)
            tasks.append(task)
        results = _run_tasks(tasks=tasks, num_workers=config.num_workers)
    new_verified = sum(result.verified for result in results)
    failed_runs = sum(result.returncode != 0 for result in results)
    return AutoVerusRunSummary(
        output_dir=config.output_dir,
        total_files=len(input_files),
        scheduled=len(tasks),
        existing_verified=existing_verified,
        existing_unverified=existing_unverified,
        new_verified=new_verified,
        new_unverified=len(results) - new_verified,
        failed_runs=failed_runs,
    )


__all__ = [
    "AUTOVERUS_BENCHMARK_SOURCES",
    "AUTOVERUS_RUNS_DIR",
    "AUTOVERUS_TOOL_DIR",
    "AutoVerusRunConfig",
    "AutoVerusRunSummary",
    "available_autoverus_benchmarks",
    "build_autoverus_output_dir",
    "build_autoverus_runtime_config",
    "is_correct_autoverus_output",
    "parse_phase1_examples",
    "render_autoverus_summary",
    "resolve_autoverus_config_file",
    "resolve_autoverus_input_dir",
    "run_autoverus",
]
