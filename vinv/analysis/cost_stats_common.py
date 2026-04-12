#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vinv.gen.cost_report import estimate_cost_usd


DEFAULT_PIPELINE_ROOT = REPO_ROOT / "results" / "pipeline" / "gpt-4o" / "CLEANED_VB"
DEFAULT_AUTOVERUS_ROOT = REPO_ROOT / "token_stats_autoverus"
DEFAULT_AUTOVERUS_LOG_ROOT = REPO_ROOT / "log_data"

VERUSBENCH_SUBDATASETS = ("cloverbench", "diffy", "mbpp", "misc")
ADDITIONAL_DATASET_PREFIXES = (
    ("humaneval_alphaverus", "humaneval-alphaverus"),
    ("obfuscated_verusbench", "obfuscated"),
    ("dafnybench", "dafnybench"),
    ("leetcode", "leetcode"),
)

PIPELINE_STRATEGY_LABELS = {
    "naive": "Iterative Refinement",
    "simple_simple_10": "Simple+Simple (10)",
    "z3_mut_val_10": "ExVerus",
    "z3_simple_10": "ExVerus_no_mut_val",
}

AUTOVERUS_MODEL_DIR_ALIASES = {
    "gpt-4o": "gpt4o",
    "gpt4o": "gpt4o",
    "deepseek": "deepseek",
    "deepseek-chat": "deepseek",
    "deepseek-chat-v3.1": "deepseek",
    "o4-mini": "o4-mini",
    "qwen": "qwen",
    "qwen/qwen3-coder": "qwen",
    "sonnet-4.5": "sonnet-4.5",
    "claude-sonnet-4.5": "sonnet-4.5",
    "anthropic/claude-sonnet-4.5": "sonnet-4.5",
}

AUTOVERUS_MODEL_TO_API_MODEL = {
    "gpt4o": "gpt-4o",
    "deepseek": "deepseek-chat",
    "o4-mini": "o4-mini",
    "qwen": "qwen/qwen3-coder",
    "sonnet-4.5": "claude-sonnet-4.5",
}

AUTOVERUS_BENCHMARKS = (
    "verusbench",
    "dafnybench",
    "humaneval-alphaverus",
    "leetcode",
    "obfuscated",
)

AUTOVERUS_LOG_BENCHMARK_DIRS = {
    "verusbench": "verusbench",
    "dafnybench": "dafny",
    "humaneval-alphaverus": "humaneval",
    "leetcode": "leetcode",
    "obfuscated": "obfuscated",
}


@dataclass(frozen=True)
class MetricSpec:
    key: str
    slug: str
    x_label: str
    title_suffix: str


@dataclass
class CaseBudget:
    case_key: str
    case_id: str
    case_name: str
    run_dir: str
    benchmark: str
    strategy: str
    source_kind: str
    success: bool
    result: str
    final_phase: str
    llm_calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    task_wall_clock_seconds: float | None
    raw_source_path: str
    calls: list[dict[str, Any]] = field(default_factory=list)


METRICS = (
    MetricSpec(
        key="total_tokens",
        slug="total_token_budget",
        x_label="total tokens",
        title_suffix="total-token budget",
    ),
    MetricSpec(
        key="cost_usd",
        slug="cost_usd_budget",
        x_label="cost (USD)",
        title_suffix="cost budget",
    ),
    MetricSpec(
        key="llm_calls",
        slug="llm_call_budget",
        x_label="LLM calls",
        title_suffix="LLM-call budget",
    ),
    MetricSpec(
        key="task_wall_clock_seconds",
        slug="wall_clock_seconds_budget",
        x_label="wall-clock time (seconds)",
        title_suffix="wall-clock-time budget",
    ),
)


def normalize_benchmark_filter(raw: str | None) -> str:
    if raw is None:
        return "verusbench"
    value = raw.strip().lower().replace("_", "-")
    aliases = {
        "cleaned-vb": "verusbench",
        "cleaned-vb-default": "verusbench",
        "cleaned_vb": "verusbench",
        "verusbench": "verusbench",
        "vb": "verusbench",
        "additional": "additional",
        "all": "all",
        "dafnybench": "dafnybench",
        "leetcode": "leetcode",
        "humaneval-alphaverus": "humaneval-alphaverus",
        "humaneval_alphaverus": "humaneval-alphaverus",
        "obfuscated": "obfuscated",
        "obfuscated-verusbench": "obfuscated",
        "obfuscated_verusbench": "obfuscated",
    }
    return aliases.get(value, value)


def benchmark_targets(benchmark_filter: str) -> list[str]:
    normalized = normalize_benchmark_filter(benchmark_filter)
    if normalized == "all":
        return list(AUTOVERUS_BENCHMARKS)
    if normalized == "additional":
        return [
            "dafnybench",
            "humaneval-alphaverus",
            "leetcode",
            "obfuscated",
        ]
    return [normalized]


def benchmark_matches(case_benchmark: str, benchmark_filter: str) -> bool:
    return case_benchmark in benchmark_targets(benchmark_filter)


def strategy_display_name(strategy: str) -> str:
    if strategy == "autoverus":
        return "AutoVerus"
    base_strategy, step_count = _split_steps_suffix(strategy)
    label = PIPELINE_STRATEGY_LABELS.get(base_strategy, base_strategy)
    if base_strategy != "naive" or step_count is None:
        return label
    return f"{label} ({step_count} steps)"


def _split_steps_suffix(value: str) -> tuple[str, int | None]:
    normalized = value.strip()
    match = re.match(r"^(?P<base>.+)_(?P<steps>\d+)_steps$", normalized)
    if not match:
        return normalized, None
    return match.group("base"), int(match.group("steps"))


def infer_pipeline_strategy_suffixes(strategy: str) -> list[str]:
    normalized = strategy.strip()
    base_strategy, step_count = _split_steps_suffix(normalized)
    if base_strategy == "naive" and step_count is not None:
        return [normalized]

    if normalized == "naive":
        return ["naive", "naive_*_steps"]
    if normalized.endswith("_10"):
        return [normalized, normalized[: -len("_10")]]
    return [normalized]


def _pipeline_report_suffix(report_path: Path) -> str:
    prefix = "llm_cost_report_"
    stem = report_path.stem
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return stem


def _pipeline_report_priority(
    *,
    strategy: str,
    report_path: Path,
) -> tuple[Any, ...]:
    requested = strategy.strip()
    requested_base, requested_steps = _split_steps_suffix(requested)
    report_suffix = _pipeline_report_suffix(report_path)
    report_base, report_steps = _split_steps_suffix(report_suffix)

    legacy_requested_base = (
        requested_base[: -len("_10")] if requested_base.endswith("_10") else None
    )

    if requested_steps is not None:
        return (
            int(report_base == requested_base and report_steps == requested_steps),
            int(
                legacy_requested_base is not None
                and report_base == legacy_requested_base
                and report_steps == requested_steps
            ),
            int(report_base == requested_base),
            int(report_base == legacy_requested_base),
            str(report_path),
        )

    return (
        int(
            report_base == requested_base and report_steps is None
        ),
        int(report_steps is not None),
        int(
            legacy_requested_base is not None
            and report_base == legacy_requested_base
            and report_steps is None
        ),
        int(
            legacy_requested_base is not None
            and report_base == legacy_requested_base
            and report_steps is not None
        ),
        int(report_base == requested_base),
        report_steps if report_steps is not None else -1,
        str(report_path),
    )


def normalize_autoverus_model_dir(model: str) -> str:
    normalized = model.strip()
    if normalized not in AUTOVERUS_MODEL_DIR_ALIASES:
        raise ValueError(
            f"Unsupported AutoVerus model alias '{model}'. "
            f"Known values: {sorted(AUTOVERUS_MODEL_DIR_ALIASES)}"
        )
    return AUTOVERUS_MODEL_DIR_ALIASES[normalized]


def autoverus_model_to_api_model(model: str) -> str:
    model_dir = normalize_autoverus_model_dir(model)
    return AUTOVERUS_MODEL_TO_API_MODEL[model_dir]


def autoverus_log_benchmark_dir(benchmark: str) -> str:
    normalized = normalize_benchmark_filter(benchmark)
    if normalized not in AUTOVERUS_LOG_BENCHMARK_DIRS:
        raise ValueError(
            f"Unsupported AutoVerus benchmark '{benchmark}' for log_data lookup."
        )
    return AUTOVERUS_LOG_BENCHMARK_DIRS[normalized]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _metric_value(case: CaseBudget, metric: MetricSpec) -> float:
    value = getattr(case, metric.key)
    if value is None:
        return float("inf")
    return float(value)


def infer_pipeline_case(full_id: str) -> tuple[str, str, str]:
    if full_id.startswith("verusbench_"):
        rest = full_id[len("verusbench_") :]
        for subdataset in VERUSBENCH_SUBDATASETS:
            prefix = f"{subdataset}_"
            if rest.startswith(prefix):
                return "verusbench", rest[len(prefix) :], full_id
        return "verusbench", rest, full_id

    if full_id.startswith("additional_"):
        rest = full_id[len("additional_") :]
        for raw_prefix, benchmark in ADDITIONAL_DATASET_PREFIXES:
            prefix = f"{raw_prefix}_"
            if rest.startswith(prefix):
                return benchmark, rest[len(prefix) :], full_id
        return "additional", rest, full_id

    return "unknown", full_id, full_id


def infer_autoverus_case(full_benchmark: str, row: dict[str, str]) -> tuple[str, str, str]:
    case_name = row["case_name"].strip()
    run_dir = row.get("run_dir", "").strip().lower()

    if full_benchmark == "verusbench":
        run_mapping = {
            "clover": "cloverbench",
            "diffy": "diffy",
            "mbpp": "mbpp",
            "misc": "misc",
        }
        for token, subdataset in run_mapping.items():
            if token in run_dir:
                return "verusbench", case_name, f"verusbench_{subdataset}_{case_name}"
        raise ValueError(
            f"Could not infer VerusBench subdataset from AutoVerus run_dir '{row.get('run_dir', '')}'."
        )

    if full_benchmark == "dafnybench":
        return "dafnybench", case_name, f"additional_dafnybench_{case_name}"
    if full_benchmark == "leetcode":
        return "leetcode", case_name, f"additional_leetcode_{case_name}"
    if full_benchmark == "humaneval-alphaverus":
        return (
            "humaneval-alphaverus",
            case_name,
            f"additional_humaneval_alphaverus_{case_name}",
        )
    if full_benchmark == "obfuscated":
        return (
            "obfuscated",
            case_name,
            f"additional_obfuscated_verusbench_{case_name}",
        )

    return full_benchmark, case_name, row["case_id"].strip()


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_log_wall_clock_seconds(path: Path) -> float | None:
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            prefix = line[:19]
            try:
                ts = datetime.strptime(prefix, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if first_ts is None:
                first_ts = ts
            last_ts = ts
    if first_ts is None or last_ts is None:
        return None
    return max((last_ts - first_ts).total_seconds(), 0.0)


def load_autoverus_wall_clock_seconds(
    *,
    autoverus_log_root: Path,
    model: str,
    benchmark: str,
) -> dict[str, float]:
    model_dir = normalize_autoverus_model_dir(model)
    benchmark_dir = autoverus_log_benchmark_dir(benchmark)
    log_dir = autoverus_log_root / model_dir / benchmark_dir
    if not log_dir.is_dir():
        return {}

    seconds_by_case: dict[str, float] = {}
    for path in sorted(log_dir.glob("*.time")):
        if "-" not in path.stem:
            continue
        case_name = path.stem.split("-", 1)[1]
        wall_clock_seconds = _parse_log_wall_clock_seconds(path)
        if wall_clock_seconds is None:
            continue
        seconds_by_case[case_name] = wall_clock_seconds
    return seconds_by_case


def _find_pipeline_report_paths(root: Path, strategy: str) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for suffix in infer_pipeline_strategy_suffixes(strategy):
        for path in sorted(root.rglob(f"llm_cost_report_{suffix}.json")):
            if path in seen:
                continue
            seen.add(path)
            found.append(path)
    return found


def load_pipeline_cases(
    pipeline_root: Path,
    strategy: str,
    benchmark_filter: str,
) -> dict[str, CaseBudget]:
    cases: dict[str, CaseBudget] = {}
    selected_priorities: dict[str, tuple[int, int, int, int, str]] = {}
    for report_path in _find_pipeline_report_paths(pipeline_root, strategy):
        report = _load_json(report_path)
        task = report.get("task", {})
        full_id = task.get("task_full_id") or report_path.parent.name
        benchmark, case_name, case_key = infer_pipeline_case(full_id)
        if not benchmark_matches(benchmark, benchmark_filter):
            continue

        summary = report.get("summary", {})
        final_status = report.get("final_status") or {}
        result = str(final_status.get("verification_status") or "unknown")
        success = result == "verification_pass"
        calls = list(report.get("calls") or [])
        priority = _pipeline_report_priority(strategy=strategy, report_path=report_path)
        if case_key in selected_priorities and priority <= selected_priorities[case_key]:
            continue
        selected_priorities[case_key] = priority

        cases[case_key] = CaseBudget(
            case_key=case_key,
            case_id=full_id,
            case_name=case_name,
            run_dir=str(task.get("work_dir") or report_path.parent),
            benchmark=benchmark,
            strategy=strategy,
            source_kind="pipeline",
            success=success,
            result=result,
            final_phase=str(final_status.get("last_phase") or ""),
            llm_calls=_safe_int(summary.get("llm_calls_total")),
            prompt_tokens=_safe_int(summary.get("prompt_tokens_total")),
            completion_tokens=_safe_int(summary.get("completion_tokens_total")),
            total_tokens=_safe_int(summary.get("total_tokens_total")),
            cost_usd=_safe_float(summary.get("cost_usd_total")),
            task_wall_clock_seconds=_safe_float(
                summary.get("task_wall_clock_seconds")
            ),
            raw_source_path=str(report_path),
            calls=calls,
        )
    return cases


def load_autoverus_cases(
    autoverus_root: Path,
    model: str,
    benchmark: str,
) -> dict[str, CaseBudget]:
    model_dir = normalize_autoverus_model_dir(model)
    benchmark_dir = autoverus_root / model_dir / benchmark
    if not benchmark_dir.is_dir():
        return {}

    csv_paths = sorted(benchmark_dir.glob("*_all_cases_total_budget.csv"))
    if not csv_paths:
        return {}
    if len(csv_paths) > 1:
        raise ValueError(
            f"Expected one total-budget CSV under {benchmark_dir}, found {len(csv_paths)}."
        )

    api_model = autoverus_model_to_api_model(model)
    wall_clock_seconds_by_case = load_autoverus_wall_clock_seconds(
        autoverus_log_root=DEFAULT_AUTOVERUS_LOG_ROOT,
        model=model,
        benchmark=benchmark,
    )
    cases: dict[str, CaseBudget] = {}
    with open(csv_paths[0], "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_benchmark, case_name, case_key = infer_autoverus_case(benchmark, row)
            prompt_tokens = _safe_int(row.get("total_input_tokens"))
            completion_tokens = _safe_int(row.get("total_output_tokens"))
            total_tokens = prompt_tokens + completion_tokens
            cost_usd = estimate_cost_usd(
                model=api_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            if case_key in cases:
                raise ValueError(
                    f"Duplicate AutoVerus case key '{case_key}' in {csv_paths[0]}."
                )
            cases[case_key] = CaseBudget(
                case_key=case_key,
                case_id=row["case_id"].strip(),
                case_name=case_name,
                run_dir=row.get("run_dir", "").strip(),
                benchmark=case_benchmark,
                strategy="autoverus",
                source_kind="autoverus",
                success=_safe_bool(row.get("success")),
                result=row.get("result", "").strip() or (
                    "verification_pass" if _safe_bool(row.get("success")) else "fail"
                ),
                final_phase=str(row.get("final_phase", "")).strip(),
                llm_calls=_safe_int(row.get("total_llm_calls")),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                task_wall_clock_seconds=wall_clock_seconds_by_case.get(case_name),
                raw_source_path=str(csv_paths[0]),
                calls=[],
            )
    return cases


def group_cases_by_benchmark(
    cases: dict[str, CaseBudget],
) -> dict[str, dict[str, CaseBudget]]:
    grouped: dict[str, dict[str, CaseBudget]] = {}
    for case_key, case in cases.items():
        grouped.setdefault(case.benchmark, {})[case_key] = case
    return grouped


def align_case_sets(
    cases_by_strategy: dict[str, dict[str, CaseBudget]],
    task_set_mode: str,
) -> tuple[dict[str, dict[str, CaseBudget]], list[str]]:
    non_empty_keys = [
        set(strategy_cases.keys())
        for strategy_cases in cases_by_strategy.values()
        if strategy_cases
    ]
    if not non_empty_keys:
        return cases_by_strategy, []

    if task_set_mode == "intersection":
        selected_keys = sorted(set.intersection(*non_empty_keys))
    elif task_set_mode == "union":
        selected_keys = sorted(set.union(*non_empty_keys))
    else:
        raise ValueError(
            f"Unsupported task_set_mode '{task_set_mode}'. Use intersection or union."
        )

    aligned: dict[str, dict[str, CaseBudget]] = {}
    for strategy, cases in cases_by_strategy.items():
        aligned[strategy] = {key: cases[key] for key in selected_keys if key in cases}
    return aligned, selected_keys


def total_budget_rows(cases: dict[str, CaseBudget]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in sorted(cases.values(), key=lambda item: item.case_key):
        rows.append(
            {
                "case_key": case.case_key,
                "case_id": case.case_id,
                "case_name": case.case_name,
                "run_dir": case.run_dir,
                "strategy": case.strategy,
                "benchmark": case.benchmark,
                "source_kind": case.source_kind,
                "result": case.result,
                "success": int(case.success),
                "final_phase": case.final_phase,
                "total_llm_calls": case.llm_calls,
                "total_input_tokens": case.prompt_tokens,
                "total_output_tokens": case.completion_tokens,
                "total_tokens": case.total_tokens,
                "total_cost_usd": case.cost_usd,
                "task_wall_clock_seconds": case.task_wall_clock_seconds,
            }
        )
    return rows


def _average_metric(
    cases: Iterable[CaseBudget],
    metric_name: str,
) -> float | None:
    values = [
        value
        for value in (getattr(case, metric_name) for case in cases)
        if value is not None
    ]
    if not values:
        return None
    return float(sum(values)) / len(values)


def summary_stats_rows(
    cases: dict[str, CaseBudget],
    *,
    strategy: str,
    benchmark: str,
    model: str | None = None,
    task_set_mode: str | None = None,
) -> list[dict[str, Any]]:
    case_list = list(cases.values())
    splits = {
        "all": case_list,
        "solved": [case for case in case_list if case.success],
        "failed": [case for case in case_list if not case.success],
    }
    solved_tasks = sum(1 for case in case_list if case.success)

    rows: list[dict[str, Any]] = []
    for split, selected in splits.items():
        rows.append(
            {
                "strategy": strategy,
                "strategy_label": strategy_display_name(strategy),
                "benchmark": benchmark,
                "model": model or "",
                "task_set_mode": task_set_mode or "",
                "split": split,
                "task_count": len(selected),
                "solved_tasks": solved_tasks,
                "failed_tasks": len(case_list) - solved_tasks,
                "total_tasks": len(case_list),
                "avg_total_tokens": _average_metric(selected, "total_tokens"),
                "avg_llm_calls": _average_metric(selected, "llm_calls"),
                "avg_cost_usd": _average_metric(selected, "cost_usd"),
                "avg_task_wall_clock_seconds": _average_metric(
                    selected, "task_wall_clock_seconds"
                ),
            }
        )
    return rows


def print_summary_stats(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        avg_total_tokens = row["avg_total_tokens"]
        avg_llm_calls = row["avg_llm_calls"]
        avg_cost_usd = row["avg_cost_usd"]
        avg_task_wall_clock_seconds = row["avg_task_wall_clock_seconds"]
        avg_total_tokens_text = (
            "NA" if avg_total_tokens is None else f"{avg_total_tokens:.2f}"
        )
        avg_llm_calls_text = "NA" if avg_llm_calls is None else f"{avg_llm_calls:.2f}"
        avg_cost_usd_text = "NA" if avg_cost_usd is None else f"{avg_cost_usd:.6f}"
        avg_task_wall_clock_seconds_text = (
            "NA"
            if avg_task_wall_clock_seconds is None
            else f"{avg_task_wall_clock_seconds:.2f}"
        )
        print(
            "[stats] "
            f"strategy={row['strategy']} "
            f"benchmark={row['benchmark']} "
            f"split={row['split']} "
            f"tasks={row['task_count']} "
            f"solved={row['solved_tasks']}/{row['total_tasks']} "
            f"avg_total_tokens={avg_total_tokens_text} "
            f"avg_llm_calls={avg_llm_calls_text} "
            f"avg_cost_usd={avg_cost_usd_text} "
            f"avg_task_wall_clock_seconds={avg_task_wall_clock_seconds_text}"
        )


def sorted_budget_rows(
    cases: dict[str, CaseBudget],
    metric: MetricSpec,
) -> list[dict[str, Any]]:
    budgeted_cases = [
        case for case in cases.values() if getattr(case, metric.key) is not None
    ]
    ordered_cases = sorted(
        budgeted_cases,
        key=lambda case: (_metric_value(case, metric), case.case_key),
    )
    rows: list[dict[str, Any]] = []
    tasks_passed = 0
    for rank, case in enumerate(ordered_cases, start=1):
        if case.success:
            tasks_passed += 1
        rows.append(
            {
                "rank": rank,
                "budget": getattr(case, metric.key),
                "tasks_passed": tasks_passed,
                "success": int(case.success),
                "case_key": case.case_key,
                "case_id": case.case_id,
                "case_name": case.case_name,
                "run_dir": case.run_dir,
                "strategy": case.strategy,
                "benchmark": case.benchmark,
                "source_kind": case.source_kind,
            }
        )
    return rows


def pipeline_calls_flat_rows(cases: dict[str, CaseBudget]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in sorted(cases.values(), key=lambda item: item.case_key):
        for call in case.calls:
            tokens = call.get("tokens") or {}
            costs = call.get("costs") or {}
            rows.append(
                {
                    "case_key": case.case_key,
                    "case_id": case.case_id,
                    "case_name": case.case_name,
                    "run_dir": case.run_dir,
                    "phase": case.strategy,
                    "call_index": call.get("sequence_id"),
                    "stage": call.get("prompt_type_id"),
                    "model": call.get("model"),
                    "num": call.get("num_choices"),
                    "success": int(bool(call.get("success"))),
                    "input_tokens": tokens.get("prompt_tokens"),
                    "output_tokens": tokens.get("completion_tokens"),
                    "total_tokens": tokens.get("total_tokens"),
                    "cost_usd": costs.get("cost_usd"),
                    "task_id": call.get("task_id"),
                    "started_at_utc": call.get("started_at_utc"),
                    "ended_at_utc": call.get("ended_at_utc"),
                    "wall_clock_seconds": call.get("wall_clock_seconds"),
                    "error_type": call.get("error_type"),
                }
            )
    return rows


def pipeline_calls_per_case_phase(cases: dict[str, CaseBudget]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for case in sorted(cases.values(), key=lambda item: item.case_key):
        phase_calls = []
        for call in case.calls:
            tokens = call.get("tokens") or {}
            costs = call.get("costs") or {}
            phase_calls.append(
                {
                    "call_index": call.get("sequence_id"),
                    "stage": call.get("prompt_type_id"),
                    "task_id": call.get("task_id"),
                    "model": call.get("model"),
                    "num": call.get("num_choices"),
                    "success": bool(call.get("success")),
                    "input_tokens": tokens.get("prompt_tokens"),
                    "output_tokens": tokens.get("completion_tokens"),
                    "total_tokens": tokens.get("total_tokens"),
                    "cost_usd": costs.get("cost_usd"),
                    "started_at_utc": call.get("started_at_utc"),
                    "ended_at_utc": call.get("ended_at_utc"),
                    "wall_clock_seconds": call.get("wall_clock_seconds"),
                }
            )

        payload[case.case_key] = {
            "case_key": case.case_key,
            "case_id": case.case_id,
            "case_name": case.case_name,
            "run_dir": case.run_dir,
            "success": case.success,
            "result": case.result,
            "phases": {
                case.strategy: {
                    "phase": case.strategy,
                    "call_count": case.llm_calls,
                    "input_tokens_total": case.prompt_tokens,
                    "output_tokens_total": case.completion_tokens,
                    "total_tokens_total": case.total_tokens,
                    "cost_usd_total": case.cost_usd,
                    "calls": phase_calls,
                }
            },
        }
    return payload


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=False)


def plot_budget_curves(
    *,
    rows_by_label: dict[str, list[dict[str, Any]]],
    metric: MetricSpec,
    title: str,
    output_base: Path,
) -> None:
    import matplotlib.pyplot as plt

    output_base.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 6))
    for label, rows in rows_by_label.items():
        if not rows:
            continue
        x_values = [row["budget"] for row in rows]
        y_values = [row["tasks_passed"] for row in rows]
        plt.step(x_values, y_values, where="post", linewidth=2.5, label=label)

    plt.xlabel(metric.x_label)
    plt.ylabel("solved tasks")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_base.with_suffix(".png"), dpi=200)
    plt.savefig(output_base.with_suffix(".svg"))
    plt.close()
