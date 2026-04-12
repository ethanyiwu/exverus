#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from vinv.analysis.cost_stats_common import (
    DEFAULT_AUTOVERUS_ROOT,
    REPO_ROOT,
    align_case_sets,
    benchmark_targets,
    group_cases_by_benchmark,
    load_autoverus_cases,
    load_pipeline_cases,
    normalize_benchmark_filter,
    strategy_display_name,
)


DEFAULT_MODELS = [
    "gpt-4o",
    "qwen3-coder",
    "deepseek-chat-v3.1",
    "claude-sonnet-4.5",
    "o4-mini",
]
DEFAULT_STRATEGIES = [
    "autoverus",
    "z3_mut_val_10",
    "naive_10_steps",
]
DEFAULT_PIPELINE_BASE_ROOTS = [
    REPO_ROOT / "results" / "pipeline",
    REPO_ROOT / "results" / "pipeline_final_final",
]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "results" / "avg_cost_stats_per_model"

PIPELINE_MODEL_DIR_PREFIXES = {
    "gpt-4o": ("gpt-4o",),
    "qwen3-coder": ("qwen3-coder",),
    "deepseek-chat-v3.1": ("deepseek-chat-v3.1",),
    "claude-sonnet-4.5": ("claude-sonnet-4.5",),
    "o4-mini": ("o4-mini",),
}
AUTOVERUS_MODEL_ALIASES = {
    "qwen3-coder": "qwen/qwen3-coder",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print average cost-related statistics for requested models and "
            "strategies, and save the same data as a Markdown table."
        )
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="CLEANED_VB",
        help="Benchmark filter. Default: CLEANED_VB",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help=f"Models to include. Default: {' '.join(DEFAULT_MODELS)}",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=DEFAULT_STRATEGIES,
        help=f"Strategies to include. Default: {' '.join(DEFAULT_STRATEGIES)}",
    )
    parser.add_argument(
        "--autoverus-root",
        type=Path,
        default=DEFAULT_AUTOVERUS_ROOT,
        help=f"AutoVerus token-stats root. Default: {DEFAULT_AUTOVERUS_ROOT}",
    )
    parser.add_argument(
        "--pipeline-base-roots",
        nargs="+",
        type=Path,
        default=DEFAULT_PIPELINE_BASE_ROOTS,
        help=(
            "Pipeline search roots used to resolve model-specific results "
            "directories. "
            f"Default: {' '.join(str(path) for path in DEFAULT_PIPELINE_BASE_ROOTS)}"
        ),
    )
    parser.add_argument(
        "--task-set-mode",
        choices=["available", "intersection", "union"],
        default="available",
        help=(
            "How to align case sets across strategies within each model. "
            "Default: available."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    return parser.parse_args()


def _benchmark_dir_candidates(raw_benchmark: str) -> list[str]:
    raw = raw_benchmark.strip()
    normalized = normalize_benchmark_filter(raw_benchmark)
    candidates: list[str] = []
    for value in (raw, raw.upper(), raw.lower(), raw.replace("-", "_")):
        if value and value not in candidates:
            candidates.append(value)
    if normalized == "verusbench" and "CLEANED_VB" not in candidates:
        candidates.append("CLEANED_VB")
    return candidates


def _pipeline_root_priority(model: str, candidate_root: Path) -> tuple[int, str]:
    model_dir = (
        candidate_root.parent.name
        if candidate_root.name == "CLEANED_VB"
        else candidate_root.name
    )
    if model_dir == model:
        return (0, model_dir)
    if model_dir.endswith("_rerun_final"):
        return (1, model_dir)
    if model_dir.endswith("_final"):
        return (2, model_dir)
    return (10, model_dir)


def iter_pipeline_candidate_roots(
    *,
    model: str,
    benchmark: str,
    pipeline_base_roots: list[Path],
) -> list[Path]:
    prefixes = PIPELINE_MODEL_DIR_PREFIXES.get(model, (model,))
    benchmark_dirs = _benchmark_dir_candidates(benchmark)
    candidates: list[Path] = []
    seen: set[Path] = set()

    for base_root in pipeline_base_roots:
        if not base_root.is_dir():
            continue
        for model_dir in sorted(base_root.iterdir()):
            if not model_dir.is_dir():
                continue
            if not any(model_dir.name.startswith(prefix) for prefix in prefixes):
                continue

            candidate_root = None
            for benchmark_dir in benchmark_dirs:
                resolved = model_dir / benchmark_dir
                if resolved.is_dir():
                    candidate_root = resolved
                    break
            if candidate_root is None:
                candidate_root = model_dir

            resolved_candidate = candidate_root.resolve()
            if resolved_candidate in seen:
                continue
            seen.add(resolved_candidate)
            candidates.append(candidate_root)

    return candidates


def _merge_benchmark_cases(
    cases: dict[str, object],
    benchmark_filter: str,
) -> dict[str, object]:
    grouped = group_cases_by_benchmark(cases)
    merged: dict[str, object] = {}
    for benchmark in benchmark_targets(benchmark_filter):
        merged.update(grouped.get(benchmark, {}))
    return merged


def load_best_pipeline_cases(
    *,
    model: str,
    strategy: str,
    benchmark: str,
    pipeline_base_roots: list[Path],
) -> tuple[dict[str, object], Path | None]:
    best_cases: dict[str, object] = {}
    best_root: Path | None = None
    best_count = -1
    best_priority: tuple[int, str] | None = None

    for candidate_root in iter_pipeline_candidate_roots(
        model=model,
        benchmark=benchmark,
        pipeline_base_roots=pipeline_base_roots,
    ):
        candidate_cases = load_pipeline_cases(
            pipeline_root=candidate_root,
            strategy=strategy,
            benchmark_filter=benchmark,
        )
        selected_cases = _merge_benchmark_cases(candidate_cases, benchmark)
        candidate_count = len(selected_cases)
        candidate_priority = _pipeline_root_priority(model, candidate_root)
        if (
            candidate_count > best_count
            or (
                candidate_count == best_count
                and best_priority is not None
                and candidate_priority < best_priority
            )
        ):
            best_count = candidate_count
            best_priority = candidate_priority
            best_cases = selected_cases
            best_root = candidate_root

    return best_cases, best_root


def load_autoverus_cases_for_targets(
    *,
    autoverus_root: Path,
    model: str,
    benchmark_filter: str,
) -> dict[str, object]:
    merged: dict[str, object] = {}
    resolved_model = AUTOVERUS_MODEL_ALIASES.get(model, model)
    for benchmark in benchmark_targets(benchmark_filter):
        merged.update(
            load_autoverus_cases(
                autoverus_root=autoverus_root,
                model=resolved_model,
                benchmark=benchmark,
            )
        )
    return merged


def average_metric(cases: list[object], attr_name: str) -> float | None:
    values = [
        value
        for value in (getattr(case, attr_name) for case in cases)
        if value is not None
    ]
    if not values:
        return None
    return float(sum(values)) / len(values)


def build_row(
    *,
    model: str,
    strategy: str,
    cases: dict[str, object],
) -> dict[str, object]:
    case_list = list(cases.values())
    return {
        "model": model,
        "strategy": strategy,
        "strategy_label": strategy_display_name(strategy),
        "cases": len(case_list),
        "avg_input_tokens": average_metric(case_list, "prompt_tokens"),
        "avg_output_tokens": average_metric(case_list, "completion_tokens"),
        "avg_total_tokens": average_metric(case_list, "total_tokens"),
        "avg_llm_calls": average_metric(case_list, "llm_calls"),
        "avg_cost_usd": average_metric(case_list, "cost_usd"),
        "avg_task_wall_clock_seconds": average_metric(
            case_list, "task_wall_clock_seconds"
        ),
    }


def _format_count(value: object) -> str:
    return str(value)


def _format_tokens_k(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value / 1000.0:.1f}"


def _format_float(value: float | None, decimals: int) -> str:
    if value is None:
        return "NA"
    return f"{value:.{decimals}f}"


def render_console_table(rows: list[dict[str, object]]) -> str:
    headers = [
        "Model",
        "Strategy",
        "Avg Total Tok (K)",
        "Avg Cost ($)",
        "Avg Time (s)",
    ]
    rendered_rows = []
    for row in rows:
        rendered_rows.append(
            [
                str(row["model"]),
                str(row["strategy_label"]),
                _format_tokens_k(row["avg_total_tokens"]),
                _format_float(row["avg_cost_usd"], 3),
                _format_float(row["avg_task_wall_clock_seconds"], 2),
            ]
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rendered_rows))
        for index in range(len(headers))
    ]
    lines = [
        " | ".join(
            header.ljust(widths[index]) for index, header in enumerate(headers)
        ),
        "-+-".join("-" * width for width in widths),
    ]
    for row in rendered_rows:
        lines.append(
            " | ".join(
                value.ljust(widths[index]) for index, value in enumerate(row)
            )
        )
    return "\n".join(lines)


def render_markdown_table(rows: list[dict[str, object]]) -> str:
    headers = [
        "Model",
        "Strategy",
        "Avg Total Tok (K)",
        "Avg Cost ($)",
        "Avg Time (s)",
    ]
    aligns = ["---", "---", "---:", "---:", "---:"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(aligns) + " |",
    ]
    for row in rows:
        values = [
            str(row["model"]),
            str(row["strategy_label"]),
            _format_tokens_k(row["avg_total_tokens"]),
            _format_float(row["avg_cost_usd"], 3),
            _format_float(row["avg_task_wall_clock_seconds"], 2),
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def sanitize_output_benchmark_name(raw_benchmark: str) -> str:
    value = raw_benchmark.strip()
    if not value:
        value = normalize_benchmark_filter(raw_benchmark)
    return value.replace("/", "_")


def main() -> None:
    args = parse_args()
    benchmark_filter = normalize_benchmark_filter(args.benchmark)
    autoverus_root = args.autoverus_root.resolve()
    pipeline_base_roots = [path.resolve() for path in args.pipeline_base_roots]
    output_root = args.output_dir.resolve()

    if not autoverus_root.is_dir():
        raise FileNotFoundError(f"AutoVerus root not found: {autoverus_root}")

    rows: list[dict[str, object]] = []
    info_lines: list[str] = []

    for model in args.models:
        cases_by_strategy: dict[str, dict[str, object]] = {}

        for strategy in args.strategies:
            if strategy == "autoverus":
                strategy_cases = load_autoverus_cases_for_targets(
                    autoverus_root=autoverus_root,
                    model=model,
                    benchmark_filter=benchmark_filter,
                )
                info_lines.append(
                    f"[info] model={model} strategy={strategy} "
                    f"cases={len(strategy_cases)} source={autoverus_root}"
                )
            else:
                strategy_cases, pipeline_root = load_best_pipeline_cases(
                    model=model,
                    strategy=strategy,
                    benchmark=benchmark_filter,
                    pipeline_base_roots=pipeline_base_roots,
                )
                if pipeline_root is None:
                    info_lines.append(
                        f"[warn] model={model} strategy={strategy} "
                        "cases=0 source=not found"
                    )
                else:
                    info_lines.append(
                        f"[info] model={model} strategy={strategy} "
                        f"cases={len(strategy_cases)} source={pipeline_root}"
                    )
            cases_by_strategy[strategy] = strategy_cases

        if args.task_set_mode != "available":
            non_empty_cases = {
                strategy: cases
                for strategy, cases in cases_by_strategy.items()
                if cases
            }
            aligned_cases = {
                strategy: {}
                for strategy in cases_by_strategy
            }
            if non_empty_cases:
                aligned_non_empty, _ = align_case_sets(
                    non_empty_cases,
                    args.task_set_mode,
                )
                aligned_cases.update(aligned_non_empty)
            cases_by_strategy = aligned_cases

        for strategy in args.strategies:
            rows.append(
                build_row(
                    model=model,
                    strategy=strategy,
                    cases=cases_by_strategy.get(strategy, {}),
                )
            )

    table = render_console_table(rows)
    for line in info_lines:
        print(line)
    print()
    print(table)

    output_dir = output_root / sanitize_output_benchmark_name(args.benchmark)
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "avg_cost_stats.md"
    markdown_lines = [
        f"# Average Cost Stats for {args.benchmark}",
        "",
        f"Task set mode: `{args.task_set_mode}`.",
        "",
        render_markdown_table(rows),
        "",
    ]
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    print()
    print(f"[ok] wrote markdown table: {markdown_path}")


if __name__ == "__main__":
    main()
