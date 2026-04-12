#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from vinv.analysis.cost_stats_common import (
    DEFAULT_AUTOVERUS_ROOT,
    DEFAULT_PIPELINE_ROOT,
    METRICS,
    REPO_ROOT,
    align_case_sets,
    benchmark_targets,
    group_cases_by_benchmark,
    load_autoverus_cases,
    load_pipeline_cases,
    normalize_benchmark_filter,
    normalize_autoverus_model_dir,
    print_summary_stats,
    plot_budget_curves,
    sorted_budget_rows,
    strategy_display_name,
    summary_stats_rows,
    total_budget_rows,
    write_csv,
)


DEFAULT_OUTPUT_DIR = REPO_ROOT / "results" / "cost_strategy_comparison"
DEFAULT_STRATEGIES = [
    "z3_mut_val_10",
    "simple_simple_10",
    "z3_simple_10",
    "naive",
    "autoverus",
]


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _format_markdown_summary_value(
    value: float | None,
    *,
    decimals: int,
) -> str:
    if value is None:
        return "NA"
    return f"{value:.{decimals}f}"


def _format_markdown_summary_tokens(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value / 1000.0:.1f}"


def _format_markdown_summary_cost(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.3f}"


def render_markdown_summary_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No aligned summary statistics available."

    split_rows_by_strategy: dict[str, dict[str, dict[str, Any]]] = {}
    strategy_labels: dict[str, str] = {}
    split_order = ("all", "solved", "failed")

    def _format_split_triplet(
        split_rows: dict[str, dict[str, Any]],
        metric_name: str,
        formatter,
    ) -> str:
        return " / ".join(
            formatter(split_rows.get(split, {}).get(metric_name))
            for split in split_order
        )

    for row in rows:
        strategy = str(row["strategy"])
        split = str(row.get("split") or "all")
        split_rows_by_strategy.setdefault(strategy, {})[split] = row
        strategy_labels[strategy] = str(row["strategy_label"])

    headers = [
        "Strategy",
        "Avg Time (s)",
        "Avg Tokens (K)",
        "Avg Cost ($)",
    ]
    aligns = ["---"] + ["---:"] * (len(headers) - 1)
    lines = [
        "Values are shown as `all / solved / failed`.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(aligns) + " |",
    ]

    for strategy, split_rows in split_rows_by_strategy.items():
        formatted_values = [
            _escape_markdown_cell(strategy_labels[strategy]),
            _format_split_triplet(
                split_rows,
                "avg_task_wall_clock_seconds",
                lambda value: _format_markdown_summary_value(value, decimals=2),
            ),
            _format_split_triplet(
                split_rows,
                "avg_total_tokens",
                _format_markdown_summary_tokens,
            ),
            _format_split_triplet(
                split_rows,
                "avg_cost_usd",
                _format_markdown_summary_cost,
            ),
        ]
        lines.append(
            "| "
            + " | ".join(formatted_values)
            + " |"
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build unified solved-vs-budget comparison plots across pipeline "
            "strategies and AutoVerus."
        )
    )
    parser.add_argument(
        "--pipeline-root",
        type=Path,
        default=DEFAULT_PIPELINE_ROOT,
        help=f"Pipeline results root. Default: {DEFAULT_PIPELINE_ROOT}",
    )
    parser.add_argument(
        "--autoverus-root",
        type=Path,
        default=DEFAULT_AUTOVERUS_ROOT,
        help=f"AutoVerus token-stats root. Default: {DEFAULT_AUTOVERUS_ROOT}",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help=(
            "Model alias for AutoVerus stats. Examples: gpt-4o, deepseek, "
            "o4-mini, qwen, sonnet-4.5."
        ),
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="CLEANED_VB",
        help=(
            "Benchmark filter. Examples: CLEANED_VB, verusbench, additional, "
            "dafnybench, humaneval-alphaverus, leetcode, obfuscated, all."
        ),
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=DEFAULT_STRATEGIES,
        help=(
            "Strategies to compare. Use 'autoverus' to include AutoVerus. "
            "Suffixed pipeline names like 'naive_20_steps' are also supported. "
            f"Default: {' '.join(DEFAULT_STRATEGIES)}"
        ),
    )
    parser.add_argument(
        "--task-set-mode",
        choices=["intersection", "union"],
        default="intersection",
        help=(
            "How to align cases across strategies before plotting. "
            "Default: intersection."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--markdown-summary-table",
        action="store_true",
        help=(
            "Also write a Markdown table summarizing aligned average time, "
            "tokens, and dollars for each strategy."
        ),
    )
    return parser.parse_args()


def load_strategy_cases_for_benchmark(
    *,
    strategy: str,
    benchmark: str,
    pipeline_root: Path,
    autoverus_root: Path,
    model: str,
) -> dict[str, Any]:
    if strategy == "autoverus":
        return load_autoverus_cases(
            autoverus_root=autoverus_root,
            model=model,
            benchmark=benchmark,
        )

    return load_pipeline_cases(
        pipeline_root=pipeline_root,
        strategy=strategy,
        benchmark_filter=benchmark,
    )


def benchmark_output_dir(
    *,
    output_root: Path,
    model: str,
    benchmark: str,
) -> Path:
    model_dir = normalize_autoverus_model_dir(model)
    return output_root / model_dir / benchmark


def write_comparison_outputs(
    *,
    benchmark: str,
    model: str,
    cases_by_strategy: dict[str, dict[str, Any]],
    task_set_mode: str,
    output_root: Path,
    markdown_summary_table: bool,
) -> None:
    benchmark_dir = benchmark_output_dir(
        output_root=output_root,
        model=model,
        benchmark=benchmark,
    )
    aligned_cases, selected_keys = align_case_sets(cases_by_strategy, task_set_mode)

    summary_rows = []
    aligned_stats_rows = []
    for strategy, strategy_cases in cases_by_strategy.items():
        aligned = aligned_cases.get(strategy, {})
        summary_rows.append(
            {
                "strategy": strategy,
                "strategy_label": strategy_display_name(strategy),
                "available_cases": len(strategy_cases),
                "aligned_cases": len(aligned),
                "aligned_solved_cases": sum(
                    1 for case in aligned.values() if case.success
                ),
                "task_set_mode": task_set_mode,
                "benchmark": benchmark,
                "model": model,
            }
        )
        aligned_stats_rows.extend(
            summary_stats_rows(
                aligned,
                strategy=strategy,
                benchmark=benchmark,
                model=model,
                task_set_mode=task_set_mode,
            )
        )
    write_csv(benchmark_dir / "case_coverage.csv", summary_rows)
    write_csv(benchmark_dir / "aligned_case_summary_stats.csv", aligned_stats_rows)
    if markdown_summary_table:
        markdown_table = render_markdown_summary_table(aligned_stats_rows)
        markdown_path = benchmark_dir / "aligned_case_summary_stats.md"
        markdown_path.write_text(markdown_table + "\n", encoding="utf-8")
        print(f"[ok] wrote markdown summary: {markdown_path}")
    print_summary_stats(aligned_stats_rows)

    if task_set_mode == "intersection" and not selected_keys:
        print(f"[skip] benchmark={benchmark} has empty case intersection")
        return

    plotted_strategy_count = 0
    for metric in METRICS:
        rows_by_label = {}
        combined_rows = []
        aligned_budget_rows = []
        for strategy, aligned in aligned_cases.items():
            if not aligned:
                continue
            label = strategy_display_name(strategy)
            rows = sorted_budget_rows(aligned, metric)
            rows_by_label[label] = rows
            for row in rows:
                combined_rows.append(
                    {
                        "strategy": strategy,
                        "strategy_label": label,
                        **row,
                    }
                )
            for row in total_budget_rows(aligned):
                aligned_budget_rows.append(
                    {
                        "strategy_label": label,
                        **row,
                    }
                )

        if not rows_by_label:
            print(f"[skip] benchmark={benchmark} metric={metric.key} has no rows")
            continue

        plotted_strategy_count = max(plotted_strategy_count, len(rows_by_label))
        write_csv(
            benchmark_dir / f"comparison_vs_{metric.slug}.csv",
            combined_rows,
        )
        write_csv(
            benchmark_dir / "aligned_case_budgets.csv",
            aligned_budget_rows,
        )
        plot_budget_curves(
            rows_by_label=rows_by_label,
            metric=metric,
            title=(
                f"{benchmark} solved tasks vs {metric.title_suffix}"
            ),
            output_base=benchmark_dir / f"comparison_vs_{metric.slug}",
        )

    print(
        f"[ok] benchmark={benchmark} strategies={plotted_strategy_count} "
        f"task_set_mode={task_set_mode}"
    )


def main() -> None:
    args = parse_args()
    pipeline_root = args.pipeline_root.resolve()
    autoverus_root = args.autoverus_root.resolve()
    output_root = args.output_dir.resolve()
    benchmark_filter = normalize_benchmark_filter(args.benchmark)

    if not pipeline_root.is_dir():
        raise FileNotFoundError(f"Pipeline root not found: {pipeline_root}")
    if "autoverus" in args.strategies and not autoverus_root.is_dir():
        raise FileNotFoundError(f"AutoVerus root not found: {autoverus_root}")

    targets = benchmark_targets(benchmark_filter)
    for benchmark in targets:
        cases_by_strategy = {}
        for strategy in args.strategies:
            strategy_cases = load_strategy_cases_for_benchmark(
                strategy=strategy,
                benchmark=benchmark,
                pipeline_root=pipeline_root,
                autoverus_root=autoverus_root,
                model=args.model,
            )
            if not strategy_cases:
                print(
                    f"[skip] benchmark={benchmark} strategy={strategy} "
                    "has no cases"
                )
                continue
            grouped = group_cases_by_benchmark(strategy_cases)
            cases_by_strategy[strategy] = grouped.get(benchmark, strategy_cases)

        if not cases_by_strategy:
            print(f"[skip] benchmark={benchmark} has no strategies to plot")
            continue

        write_comparison_outputs(
            benchmark=benchmark,
            model=args.model,
            cases_by_strategy=cases_by_strategy,
            task_set_mode=args.task_set_mode,
            output_root=output_root,
            markdown_summary_table=args.markdown_summary_table,
        )


if __name__ == "__main__":
    main()
