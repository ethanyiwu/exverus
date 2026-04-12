import json
from typing import Dict, List, Tuple

from fire import Fire

from vinv.analysis.classify_task import (
    count_num_assertions,
    count_num_invariants,
    count_num_proof,
)
from vinv.config import (
    AUTOVERUS_ADDITONAL_RESULT_JSON_FILE,
    AUTOVERUS_CLEANED_VB_RESULT_JSON_FILE,
    PIPELINE_ADDITONAL_RESULT_JSON_FILE,
    PIPELINE_CLEANED_VB_RESULT_JSON_FILE,
    RESULTS_ROOT_DIR,
)
from vinv.data.cherrypick import get_all_vb_proofs


def parse_autoverus_result_all():
    autoverus_result_status: Dict[str, str] = {}
    for src in ("CLEANED_VB", "ADDITIONAL"):
        with open(
            AUTOVERUS_CLEANED_VB_RESULT_JSON_FILE
            if src == "CLEANED_VB"
            else AUTOVERUS_ADDITONAL_RESULT_JSON_FILE,
            "r",
        ) as f:
            data = json.load(f)

        for _, value in data.items():
            task_name = value["case_name"]
            last_repaired_path = value["last_repaired_code_path"]
            benchmark = (
                last_repaired_path.split("/")[-2]
                .split("-")[2]
                .replace("clover", "cloverbench")
                .replace("dafny", "dafnybench")
                .replace("humaneval", "humaneval_alphaverus")
                .replace("obfuscated", "obfuscated_verusbench")
            )
            task_id = f"{benchmark}_{task_name}"
            autoverus_result_status[task_id] = value["verification_status"]

    return autoverus_result_status


def parse_pipeline_result_all():
    pipeline_result_status: Dict[str, str] = {}
    # CLEANED_VB
    with open(PIPELINE_CLEANED_VB_RESULT_JSON_FILE, "r") as f:
        data = json.load(f)
        for task_full_id, value in data.items():
            task_id = task_full_id[len("verusbench_") :]
            pipeline_result_status[task_id] = value["verification_status"]
    # ADDITIONAL
    with open(PIPELINE_ADDITONAL_RESULT_JSON_FILE, "r") as f:
        data = json.load(f)
        for task_full_id, value in data.items():
            task_id = task_full_id[len("additional_") :]
            pipeline_result_status[task_id] = value["verification_status"]

    return pipeline_result_status


def get_autoverus_result_status(task_id: str):
    autoverus_result_status = parse_autoverus_result_all()
    return autoverus_result_status.get(task_id)


def main():
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

    autoverus_result_status = parse_autoverus_result_all()
    pipeline_result_status = parse_pipeline_result_all()

    # collect metrics per proof
    per_proof_rows: List[Dict[str, int | str]] = []
    invariants_counts: List[int] = []
    assertions_counts: List[int] = []
    proof_fn_counts: List[int] = []

    cleaned_task_ids = {p.task_id for p in proofs_cleaned}
    for proof in all_verified_proofs:
        num_invariants = count_num_invariants(proof)
        num_assertions = count_num_assertions(proof)
        num_proof = count_num_proof(proof)

        invariants_counts.append(num_invariants)
        assertions_counts.append(num_assertions)
        proof_fn_counts.append(num_proof)

        per_proof_rows.append(
            {
                "task_id": proof.task_id,
                "invariants": num_invariants,
                "assertions": num_assertions,
                "proofs": num_proof,
                "source": "CLEANED_VB"
                if proof.task_id in cleaned_task_ids
                else "ADDITIONAL",
            }
        )

    a_inv = 5
    a_asr = 1
    a_prf = 1

    # compute distribution for each metric
    def dist(values: List[int], a: int) -> Tuple[int, int]:
        low = sum(1 for v in values if v < a)
        high = sum(1 for v in values if v >= a)
        return low, high

    inv_dist = dist(invariants_counts, a_inv)
    asr_dist = dist(assertions_counts, a_asr)
    prf_dist = dist(proof_fn_counts, a_prf)

    print("=" * 80)
    print("Sources: CLEANED_VB + ADDITIONAL")
    print(f"Num proofs: {len(all_verified_proofs)}")
    print(
        "- Invariants threshold: a =",
        a_inv,
        " => counts (low, high)=",
        inv_dist,
    )
    print(
        "- Assertions threshold: a =",
        a_asr,
        " => counts (w/o, w/)=",
        asr_dist,
    )
    print(
        "- Proofs threshold: a =",
        a_prf,
        " => counts (w/o, w/)=",
        prf_dist,
    )

    aggregated_results = {}
    # show per-task classification summary
    def classify_low_high(value: int, a: int) -> str:
        return "low" if value < a else "high"

    for row in per_proof_rows:
        inv_grp = classify_low_high(int(row["invariants"]), a_inv)
        asr_grp = classify_low_high(int(row["assertions"]), a_asr)
        prf_grp = classify_low_high(int(row["proofs"]), a_prf)
        autoverus_result = autoverus_result_status.get(row["task_id"])
        pipeline_result = pipeline_result_status.get(row["task_id"])
        benchmark = row["task_id"].split("_", 1)[0]
        # print(
        #     f"{row['task_id']}: inv={row['invariants']}({inv_grp}), asr={row['assertions']}({asr_grp}), proof={row['proofs']}({prf_grp}), autoverus={autoverus_result}, pipeline={pipeline_result}"
        # )
        aggregated_results[row["task_id"]] = {
            "autoverus": autoverus_result,
            "pipeline": pipeline_result,
            "invariants": row["invariants"],
            "assertions": row["assertions"],
            "proofs": row["proofs"],
            "inv_grp": inv_grp,
            "asr_grp": asr_grp,
            "prf_grp": prf_grp,
            "benchmark": benchmark,
            "source": row["source"],
        }

    # write aggregated_results to a json file
    with open(RESULTS_ROOT_DIR / "aggregated_difficulty_results.json", "w") as f:
        json.dump(aggregated_results, f, indent=4)

    # number of solved tasks of each group
    print("\n" + "=" * 80)
    print("Solved counts per group (xx/yy), by technique")
    metrics = [
        ("inv_grp", "invariants"),
        ("asr_grp", "assertions"),
        ("prf_grp", "proofs"),
    ]
    groups = ["low", "high"]

    def format_group_label(metric_key: str, g: str) -> str:
        if metric_key == "inv_grp":
            return g
        # for assertions and proofs, map low->w/o (0), high->w/ (>=1)
        return "w/o" if g == "low" else "w/"

    for grp_key, label in metrics:
        print(f"[Metric: {label}]")
        for g in groups:
            total = sum(
                1 for _, info in aggregated_results.items() if info[grp_key] == g
            )
            autoverus_solved = sum(
                1
                for _, info in aggregated_results.items()
                if info[grp_key] == g and info["autoverus"] == "verification_pass"
            )
            pipeline_solved = sum(
                1
                for _, info in aggregated_results.items()
                if info[grp_key] == g and info["pipeline"] == "verification_pass"
            )
            print(
                f"- {format_group_label(grp_key, g)}: autoverus {autoverus_solved}/{total}, pipeline {pipeline_solved}/{total}"
            )
        print("")

    # per sub-dataset breakdown
    benchmarks = sorted({info["benchmark"] for info in aggregated_results.values()})
    print("\n" + "=" * 80)
    print("Per sub-dataset results")
    for bench in benchmarks:
        bench_infos = [
            info for info in aggregated_results.values() if info["benchmark"] == bench
        ]
        inv_counts_b = [int(info["invariants"]) for info in bench_infos]
        asr_counts_b = [int(info["assertions"]) for info in bench_infos]
        prf_counts_b = [int(info["proofs"]) for info in bench_infos]

        inv_dist_b = dist(inv_counts_b, a_inv)
        asr_dist_b = dist(asr_counts_b, a_asr)
        prf_dist_b = dist(prf_counts_b, a_prf)

        print(f"[Sub-dataset: {bench}]")
        print(
            "- Invariants threshold: a =",
            a_inv,
            " => counts (low, high)=",
            inv_dist_b,
        )
        print(
            "- Assertions threshold: a =",
            a_asr,
            " => counts (w/o, w/)=",
            asr_dist_b,
        )
        print(
            "- Proofs threshold: a =",
            a_prf,
            " => counts (w/o, w/)=",
            prf_dist_b,
        )

        print("Solved counts per group (xx/yy), by technique")
        for grp_key, label in metrics:
            print(f"[Metric: {label}]")
            for g in groups:
                total = sum(1 for info in bench_infos if info[grp_key] == g)
                autoverus_solved = sum(
                    1
                    for info in bench_infos
                    if info[grp_key] == g and info["autoverus"] == "verification_pass"
                )
                pipeline_solved = sum(
                    1
                    for info in bench_infos
                    if info[grp_key] == g and info["pipeline"] == "verification_pass"
                )
                print(
                    f"- {format_group_label(grp_key, g)}: autoverus {autoverus_solved}/{total}, pipeline {pipeline_solved}/{total}"
                )
            print("")

    # specific benchmark groups per request
    print("\n" + "=" * 80)
    print("Per benchmark results (requested)")

    def in_set(value: str, candidates: List[str]) -> bool:
        return value in set(candidates)

    benchmark_groups = [
        ("verusbench", lambda info: info["source"] == "CLEANED_VB"),
        ("dafny", lambda info: in_set(info["benchmark"], ["dafny", "dafnybench"])),
        (
            "humaneval",
            lambda info: in_set(
                info["benchmark"], ["humaneval", "humaneval_alphaverus"]
            ),
        ),
        ("leetcode", lambda info: info["benchmark"] == "leetcode"),
        (
            "obfuscated_verusbench",
            lambda info: in_set(
                info["benchmark"], ["obfuscated", "obfuscated_verusbench"]
            ),
        ),
    ]

    for label_name, predicate in benchmark_groups:
        group_infos = [info for info in aggregated_results.values() if predicate(info)]
        if not group_infos:
            continue

        inv_counts_g = [int(info["invariants"]) for info in group_infos]
        asr_counts_g = [int(info["assertions"]) for info in group_infos]
        prf_counts_g = [int(info["proofs"]) for info in group_infos]

        inv_dist_g = dist(inv_counts_g, a_inv)
        asr_dist_g = dist(asr_counts_g, a_asr)
        prf_dist_g = dist(prf_counts_g, a_prf)

        print(f"[Benchmark: {label_name}]")
        print(
            "- Invariants threshold: a =",
            a_inv,
            " => counts (low, high)=",
            inv_dist_g,
        )
        print(
            "- Assertions threshold: a =",
            a_asr,
            " => counts (w/o, w/)=",
            asr_dist_g,
        )
        print(
            "- Proofs threshold: a =",
            a_prf,
            " => counts (w/o, w/)=",
            prf_dist_g,
        )

        print("Solved counts per group (xx/yy), by technique")
        for grp_key, metric_label in metrics:
            print(f"[Metric: {metric_label}]")
            for g in groups:
                total = sum(1 for info in group_infos if info[grp_key] == g)
                autoverus_solved = sum(
                    1
                    for info in group_infos
                    if info[grp_key] == g and info["autoverus"] == "verification_pass"
                )
                pipeline_solved = sum(
                    1
                    for info in group_infos
                    if info[grp_key] == g and info["pipeline"] == "verification_pass"
                )
                print(
                    f"- {format_group_label(grp_key, g)}: autoverus {autoverus_solved}/{total}, pipeline {pipeline_solved}/{total}"
                )
            print("")

    # comprehensive LaTeX table for requested benchmarks
    print("\n" + "=" * 80)
    print("LaTeX table (requested benchmarks)")

    def bench_macro(name: str) -> str:
        mapping = {
            "verusbench": r"\verusbench",
            "dafny": r"\dafnybench",
            "humaneval": r"\humanevalbench",
            "leetcode": r"\lcbench",
            "obfuscated_verusbench": r"\obfsbench",
        }
        return mapping.get(name, name)

    # Build a single table: Benchmark, Technique, then metrics groups
    header = []
    header.append("\\begin{tabular}{l|l|c|c|c|c|c|c}")
    header.append("        \\toprule")
    header.append(
        "Benchmark & Technique & \\multicolumn{2}{c|}{invariants} & \\multicolumn{2}{c|}{assertions} & \\multicolumn{2}{c}{proofs} \\\\"
    )
    header.append(" &  & low & high & w/o & w/ & w/o & w/ \\\\")
    header.append("        \\midrule")

    lines: List[str] = []
    lines.extend(header)

    def pct_str(num: int, den: int) -> str:
        if den <= 0:
            return "0.0"
        return f"{(num/den)*100:.1f}"

    for label_name, predicate in benchmark_groups:
        group_infos = [info for info in aggregated_results.values() if predicate(info)]
        if not group_infos:
            continue

        bench_label = bench_macro(label_name)
        # Totals per metric-group
        totals = {
            "inv": {
                "low": sum(1 for info in group_infos if info["inv_grp"] == "low"),
                "high": sum(1 for info in group_infos if info["inv_grp"] == "high"),
            },
            "asr": {
                "w/o": sum(1 for info in group_infos if info["asr_grp"] == "low"),
                "w/": sum(1 for info in group_infos if info["asr_grp"] == "high"),
            },
            "prf": {
                "w/o": sum(1 for info in group_infos if info["prf_grp"] == "low"),
                "w/": sum(1 for info in group_infos if info["prf_grp"] == "high"),
            },
        }

        # Solved counts by technique
        def solved_counts(tech_key: str):
            return {
                "inv": {
                    "low": sum(
                        1
                        for info in group_infos
                        if info["inv_grp"] == "low"
                        and info[tech_key] == "verification_pass"
                    ),
                    "high": sum(
                        1
                        for info in group_infos
                        if info["inv_grp"] == "high"
                        and info[tech_key] == "verification_pass"
                    ),
                },
                "asr": {
                    "w/o": sum(
                        1
                        for info in group_infos
                        if info["asr_grp"] == "low"
                        and info[tech_key] == "verification_pass"
                    ),
                    "w/": sum(
                        1
                        for info in group_infos
                        if info["asr_grp"] == "high"
                        and info[tech_key] == "verification_pass"
                    ),
                },
                "prf": {
                    "w/o": sum(
                        1
                        for info in group_infos
                        if info["prf_grp"] == "low"
                        and info[tech_key] == "verification_pass"
                    ),
                    "w/": sum(
                        1
                        for info in group_infos
                        if info["prf_grp"] == "high"
                        and info[tech_key] == "verification_pass"
                    ),
                },
            }

        av = solved_counts("autoverus")
        pl = solved_counts("pipeline")

        # Compute percentages and bold best per group
        def bold_pair(v1: str, v2: str) -> tuple[str, str]:
            try:
                a = float(v1) if v1 != "" else None
                b = float(v2) if v2 != "" else None
            except ValueError:
                return v1, v2
            if a is None and b is None:
                return v1, v2
            if a is None:
                return v1, f"\\textbf{{{v2}}}"
            if b is None:
                return f"\\textbf{{{v1}}}", v2
            if abs(a - b) < 1e-9:
                return f"\\textbf{{{v1}}}", f"\\textbf{{{v2}}}"
            return (f"\\textbf{{{v1}}}", v2) if a > b else (v1, f"\\textbf{{{v2}}}")

        # Build rows: two techniques under each benchmark
        # Invariants
        inv_low_av = pct_str(av["inv"]["low"], totals["inv"]["low"])
        inv_low_pl = pct_str(pl["inv"]["low"], totals["inv"]["low"])
        inv_high_av = pct_str(av["inv"]["high"], totals["inv"]["high"])
        inv_high_pl = pct_str(pl["inv"]["high"], totals["inv"]["high"])
        inv_low_av, inv_low_pl = bold_pair(inv_low_av, inv_low_pl)
        inv_high_av, inv_high_pl = bold_pair(inv_high_av, inv_high_pl)

        # Assertions
        asr_wo_av = pct_str(av["asr"]["w/o"], totals["asr"]["w/o"])
        asr_wo_pl = pct_str(pl["asr"]["w/o"], totals["asr"]["w/o"])
        asr_w_av = pct_str(av["asr"]["w/"], totals["asr"]["w/"])
        asr_w_pl = pct_str(pl["asr"]["w/"], totals["asr"]["w/"])
        asr_wo_av, asr_wo_pl = bold_pair(asr_wo_av, asr_wo_pl)
        asr_w_av, asr_w_pl = bold_pair(asr_w_av, asr_w_pl)

        # Proofs
        prf_wo_av = pct_str(av["prf"]["w/o"], totals["prf"]["w/o"])
        prf_wo_pl = pct_str(pl["prf"]["w/o"], totals["prf"]["w/o"])
        prf_w_av = pct_str(av["prf"]["w/"], totals["prf"]["w/"])
        prf_w_pl = pct_str(pl["prf"]["w/"], totals["prf"]["w/"])
        prf_wo_av, prf_wo_pl = bold_pair(prf_wo_av, prf_wo_pl)
        prf_w_av, prf_w_pl = bold_pair(prf_w_av, prf_w_pl)

        lines.append(
            f"\\multirow{{2}}{{*}}{{{bench_label}}} & \\av & {inv_low_av} & {inv_high_av} & {asr_wo_av} & {asr_w_av} & {prf_wo_av} & {prf_w_av} \\\\"
        )
        lines.append(
            f" & \\tool & {inv_low_pl} & {inv_high_pl} & {asr_wo_pl} & {asr_w_pl} & {prf_wo_pl} & {prf_w_pl} \\\\"
        )
        lines.append("        \\midrule")

    # replace the last \midrule with \bottomrule
    lines[-1] = lines[-1].replace("\\midrule", "\\bottomrule")
    lines.append("\\end{tabular}")

    for line in lines:
        print(line)


if __name__ == "__main__":
    Fire(main)
