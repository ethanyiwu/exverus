import os
from typing import Dict, List, Set, Tuple

import matplotlib

# Use a non-interactive backend for headless environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib_venn as venn

from vinv.analysis.classify_task import (
    count_num_assertions,
    count_num_invariants,
    count_num_proof,
)
from vinv.analysis.table.table_difficulty_distribution import (
    parse_autoverus_result_all,
    parse_pipeline_result_all,
)
from vinv.data.cherrypick import get_all_vb_proofs


def collect_solved_sets() -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    autoverus_result_status = parse_autoverus_result_all()
    pipeline_result_status = parse_pipeline_result_all()

    autoverus_pass_tasks: Set[str] = {
        task_id
        for task_id, status in autoverus_result_status.items()
        if status == "verification_pass"
    }
    pipeline_pass_tasks: Set[str] = {
        task_id
        for task_id, status in pipeline_result_status.items()
        if status == "verification_pass"
    }

    def classify_group(task_id: str) -> str:
        tid = task_id
        if "obfuscated_verusbench" in tid:
            return "obfuscated_verusbench"
        if "humaneval_alphaverus" in tid:
            return "humaneval"
        if tid.startswith("humaneval"):
            return "humaneval"
        if tid.startswith("leetcode"):
            return "leetcode"
        if tid.startswith("dafnybench") or tid.startswith("dafny"):
            return "dafny"
        return "verusbench"

    def group_by_benchmark(tasks: Set[str]) -> Dict[str, Set[str]]:
        grouped: Dict[str, Set[str]] = {}
        for task_id in tasks:
            group = classify_group(task_id)
            grouped.setdefault(group, set()).add(task_id)
        return grouped

    autoverus_by_bench = group_by_benchmark(autoverus_pass_tasks)
    pipeline_by_bench = group_by_benchmark(pipeline_pass_tasks)

    all_benchmarks = set(autoverus_by_bench.keys()) | set(pipeline_by_bench.keys())
    for bench in all_benchmarks:
        autoverus_by_bench.setdefault(bench, set())
        pipeline_by_bench.setdefault(bench, set())

    return autoverus_by_bench, pipeline_by_bench


def draw_proportional_venn(
    ax: plt.Axes,
    left_count: int,
    both_count: int,
    right_count: int,
    left_label: str,
    right_label: str,
    show_set_labels: bool = False,
) -> None:
    """
    Draws a two-set area-proportional Venn diagram using matplotlib-venn.
    Sets a distinct purple color for the overlapping area.
    """
    subsets = (left_count, right_count, both_count)

    # Define your base colors
    left_color = "#90CAF9"  # Light blue
    right_color = "#EF9A9A"  # Light red

    # Define a color for the overlap (a shade of purple from mixing red and blue)
    # This color will be explicitly set for the intersection patch.
    overlap_color = "#B39DDB"  # A light lavender/purple

    v = venn.venn2(
        subsets=subsets,
        set_labels=(
            (left_label if show_set_labels else ""),
            (right_label if show_set_labels else ""),
        ),
        ax=ax,
        set_colors=(
            left_color,
            right_color,
        ),  # Set base colors for the individual circles
        alpha=0.6,  # This alpha will apply to the individual (non-overlapping) parts
    )

    # Apply edge colors and linewidths for the individual sections
    if v.get_patch_by_id("10"):  # Left-only region
        v.get_patch_by_id("10").set_edgecolor("#1976D2")
        v.get_patch_by_id("10").set_linewidth(1.0)

    if v.get_patch_by_id("01"):  # Right-only region
        v.get_patch_by_id("01").set_edgecolor("#C62828")
        v.get_patch_by_id("01").set_linewidth(1.0)

    # Explicitly set the facecolor for the overlapping area (patch '11')
    if v.get_patch_by_id("11"):  # Overlapping region
        v.get_patch_by_id("11").set_facecolor(overlap_color)
        v.get_patch_by_id("11").set_edgecolor(
            "grey"
        )  # Optional: Keep consistent grey edge
        v.get_patch_by_id("11").set_linewidth(1.0)
        # We can also apply an alpha to the overlap color if we want it to be translucent
        v.get_patch_by_id("11").set_alpha(0.7)  # Slightly higher alpha for the overlap

    # Style the text labels for counts (enlarged)
    for label_id in ["10", "01", "11"]:
        if v.get_label_by_id(label_id):
            # Increase font size for better readability
            v.get_label_by_id(label_id).set_fontsize(28)

    # Make the intersection count bold
    if v.get_label_by_id("11"):
        v.get_label_by_id("11").set_fontweight("bold")

    # Style the set labels only if shown
    if show_set_labels:
        for label in v.set_labels:
            if label:
                label.set_fontsize(22)


def plot_venn_per_benchmark(
    output_path: str | None = None,
    include: List[str] | None = None,
    dpi: int = 150,
    include_merged: bool = True,
) -> str:
    autoverus_by_bench, pipeline_by_bench = collect_solved_sets()

    def bench_macro(name: str) -> str:
        mapping = {
            "verusbench": "VerusBench",
            "dafny": "DafnyBench",
            "humaneval": "HumanEvalVerus",
            "leetcode": "LeetCodeBench",
            "obfuscated_verusbench": "ObfuscatedVerusBench",
            "all": "AllBenchmarks",
        }
        return mapping.get(name, name)

    def bench_macro_tex(name: str) -> str:
        mapping = {
            "verusbench": r"\verusbench",
            "dafny": r"\dafnybench",
            "humaneval": r"\humanevalbench",
            "leetcode": r"\lcbench",
            "obfuscated_verusbench": r"\obfsbench",
            "all": r"\allbenchmarks",
        }
        return mapping.get(name, name)

    def normalize_include(values: List[str]) -> Set[str]:
        reverse = {
            "VerusBench": "verusbench",
            "DafnyBench": "dafny",
            "HumanEvalVerus": "humaneval",
            "LeetCodeBench": "leetcode",
            "ObfuscatedVerusBench": "obfuscated_verusbench",
        }
        result: Set[str] = set()
        for v in values:
            if v in reverse:
                result.add(reverse[v])
            else:
                result.add(v)
        return result

    benchmarks = sorted(set(autoverus_by_bench.keys()) | set(pipeline_by_bench.keys()))
    benchmarks = [
        "verusbench",
        "dafny",
        "leetcode",
        "humaneval",
        "obfuscated_verusbench",
    ]
    if include:
        include_set = normalize_include(include)
        benchmarks = [b for b in benchmarks if b in include_set]

    benchmarks = [
        b for b in benchmarks if len(autoverus_by_bench[b] | pipeline_by_bench[b]) > 0
    ]

    if not benchmarks:
        raise RuntimeError("No benchmarks with solved tasks to plot.")

    merged_counts: Tuple[int, int, int] | None = None
    if include_merged:
        a_all: Set[str] = set()
        p_all: Set[str] = set()
        for b in benchmarks:
            a_all |= autoverus_by_bench[b]
            p_all |= pipeline_by_bench[b]
        both_all = a_all & p_all
        a_only_all = a_all - p_all
        p_only_all = p_all - a_all
        merged_counts = (len(a_only_all), len(both_all), len(p_only_all))

    os.makedirs("charts", exist_ok=True)

    saved_paths: List[str] = []
    # For LaTeX: (image_path, caption)
    per_benchmark_latex_entries: List[Tuple[str, str]] = []

    if include_merged and merged_counts is not None:
        fig, ax = plt.subplots(figsize=(5.0, 4.3))
        draw_proportional_venn(
            ax,
            left_count=merged_counts[0],
            both_count=merged_counts[1],
            right_count=merged_counts[2],
            left_label="AutoVerus",
            right_label="ExVerus",
        )
        fig.tight_layout()
        out = os.path.join("charts", "venn_all_benchmarks.png")
        fig.savefig(out, dpi=dpi)
        plt.close(fig)
        saved_paths.append(out)
        per_benchmark_latex_entries.append(
            (
                out,
                bench_macro_tex("all"),
            )
        )

    for bench in benchmarks:
        a_set = autoverus_by_bench[bench]
        p_set = pipeline_by_bench[bench]

        both = a_set & p_set
        a_only = a_set - p_set
        p_only = p_set - a_set

        fig, ax = plt.subplots(figsize=(5.0, 4.3))
        draw_proportional_venn(
            ax,
            left_count=len(a_only),
            both_count=len(both),
            right_count=len(p_only),
            left_label="AutoVerus",
            right_label="ExVerus",
        )
        fig.tight_layout()
        out = os.path.join("charts", f"venn_{bench}.png")
        fig.savefig(out, dpi=dpi)
        plt.close(fig)
        saved_paths.append(out)
        per_benchmark_latex_entries.append(
            (
                out,
                bench_macro_tex(bench),
            )
        )

    # Persist LaTeX snippet for per-benchmark group
    _write_latex_group(
        entries=per_benchmark_latex_entries,
        out_tex=os.path.join("charts", "venn_per_benchmark.tex"),
        # Simplified caption to avoid redundancy
        group_caption="Venn charts per benchmark.",
        label="fig:venn_per_benchmark",
    )

    return "charts/"


def plot_all_benchmarks_decomposition(
    output_path: str | None = None, include: List[str] | None = None, dpi: int = 150
) -> str:
    autoverus_by_bench, pipeline_by_bench = collect_solved_sets()

    def normalize_include(values: List[str]) -> Set[str]:
        reverse = {
            "VerusBench": "verusbench",
            "DafnyBench": "dafny",
            "HumanEvalVerus": "humaneval",
            "LeetCodeBench": "leetcode",
            "ObfuscatedVerusBench": "obfuscated_verusbench",
        }
        result: Set[str] = set()
        for v in values:
            result.add(reverse.get(v, v))
        return result

    benchmarks = [
        "verusbench",
        "dafny",
        "leetcode",
        "humaneval",
        "obfuscated_verusbench",
    ]
    if include:
        include_set = normalize_include(include)
        benchmarks = [b for b in benchmarks if b in include_set]

    a_all: Set[str] = set()
    p_all: Set[str] = set()
    for b in benchmarks:
        a_all |= autoverus_by_bench.get(b, set())
        p_all |= pipeline_by_bench.get(b, set())

    combined_any = a_all | p_all

    proofs_cleaned = get_all_vb_proofs(
        verified_proof=True,
        use_specified_taskids=False,
        with_invariant=False,
        remove_blacklisted=True,
        source="CLEANED_VB",
    )
    proofs_additional = get_all_vb_proofs(
        verified_proof=True,
        use_specified_taskids=False,
        with_invariant=False,
        remove_blacklisted=True,
        source="ADDITIONAL",
    )
    all_verified_proofs = proofs_cleaned + proofs_additional

    a_inv = 5
    a_asr = 1
    a_prf = 1

    metrics: Dict[str, Tuple[int, int, int]] = {}
    for proof in all_verified_proofs:
        t = proof.task_id
        metrics[t] = (
            count_num_invariants(proof),
            count_num_assertions(proof),
            count_num_proof(proof),
        )

    def group_mask(metric_idx: int, threshold: int) -> Tuple[Set[str], Set[str]]:
        low: Set[str] = set()
        high: Set[str] = set()
        for task_id, triple in metrics.items():
            value = triple[metric_idx]
            (low if value < threshold else high).add(task_id)
        return low, high

    inv_low, inv_high = group_mask(0, a_inv)
    asr_low, asr_high = group_mask(1, a_asr)
    prf_low, prf_high = group_mask(2, a_prf)

    def counts_for_subset(task_subset: Set[str]) -> Tuple[int, int, int, int]:
        subset = combined_any & task_subset
        a_only = len((a_all - p_all) & subset)
        both = len((a_all & p_all) & subset)
        p_only = len((p_all - a_all) & subset)
        total = a_only + both + p_only
        return a_only, both, p_only, total

    os.makedirs("charts", exist_ok=True)

    metric_groups = [
        ("invariants_low", "Invariants <5", inv_low),
        ("invariants_high", "Invariants >=5", inv_high),
        ("assertions_wo", "Assertions w/o", asr_low),
        ("assertions_w", "Assertions w/", asr_high),
        ("proofs_wo", "Proofs w/o", prf_low),
        ("proofs_w", "Proofs w/", prf_high),
    ]

    # For LaTeX: (image_path, caption)
    per_metric_latex_entries: List[Tuple[str, str]] = []

    for slug, title, group_set in metric_groups:
        a_only, both, p_only, tot = counts_for_subset(group_set)
        fig, ax = plt.subplots(figsize=(5.0, 4.3))
        draw_proportional_venn(ax, a_only, both, p_only, "AutoVerus", "ExVerus")
        fig.tight_layout()
        out = os.path.join("charts", f"venn_all_{slug}.png")
        fig.savefig(out, dpi=dpi)
        plt.close(fig)
        per_metric_latex_entries.append(
            (
                out,
                f"{title}",
            )
        )
    # Persist LaTeX snippet for per-metric group
    _write_latex_group(
        entries=per_metric_latex_entries,
        out_tex=os.path.join("charts", "venn_per_metrics.tex"),
        group_caption="All-benchmarks Venn charts by metric groups.",
        label="fig:venn_per_metrics",
    )

    return "charts/"


def _write_latex_group(
    entries: List[Tuple[str, str]], out_tex: str, group_caption: str, label: str
) -> None:
    # Build a single row (1x6) using subfigures
    lines: List[str] = []
    lines.append("% Auto-generated by vinv.analysis.figure.venn_chart")
    lines.append(
        "% Requires: \\usepackage{graphicx} \\usepackage{subcaption} \\usepackage{xcolor}"
    )
    lines.append("\\begin{figure}[p]")
    lines.append("  \\centering")
    # Smaller subfigure captions; slightly smaller main caption
    lines.append("  \\captionsetup[sub]{font=footnotesize}")
    lines.append("  \\captionsetup{font=small}")

    for idx, (img, caption) in enumerate(entries):
        lines.append("  \\begin{subfigure}{0.16\\textwidth}")
        lines.append("    \\centering")
        lines.append(f"    \\includegraphics[width=\\linewidth]{{{img}}}")
        lines.append(f"    \\caption{{{caption}}}")
        lines.append(
            "  \\end{subfigure}" + ("\\hfill" if idx != len(entries) - 1 else "")
        )

    # Create a legend with colored text, corresponding to the chart colors.
    # The hex codes are from `draw_proportional_venn`: left_color = "#90CAF9", right_color = "#EF9A9A"
    legend_text = (
        # "AutoVerus (\\textcolor[HTML]{90CAF9}{\\large\\textbullet}); "
        # "ExVerus (\\textcolor[HTML]{EF9A9A}{\\large\\textbullet})"
        # use rectangle instead of bullet
        "AutoVerus (\\colorbox[HTML]{90CAF9}{  }); "
        "ExVerus (\\colorbox[HTML]{EF9A9A}{  })"
    )
    final_caption = f"{group_caption} {legend_text}."
    lines.append(f"  \\caption{{{final_caption}}}")
    if label:
        lines.append(f"  \\label{{{label}}}")
    lines.append("\\end{figure}")

    with open(out_tex, "w") as f:
        f.write("\n".join(lines))


def main(
    output: str | None = None,
    include: List[str] | None = None,
    dpi: int = 150,
    include_merged: bool = True,
    decompose_output: str | None = None,
):
    out_dir1 = plot_venn_per_benchmark(
        output_path=output, include=include, dpi=dpi, include_merged=include_merged
    )
    print(f"Saved per-benchmark charts under: {out_dir1}")
    out_dir2 = plot_all_benchmarks_decomposition(
        output_path=decompose_output, include=include, dpi=dpi
    )
    print(f"Saved per-metric charts under: {out_dir2}")
    print(
        "Also wrote LaTeX snippets: charts/venn_per_benchmark.tex and charts/venn_per_metrics.tex"
    )


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
