import io
import re

# --- Hyperparameter ---
# Set this to False if you only want to see the verified number (e.g., 112)
# and not the accuracy percentage (e.g., 112 / 76.7%).
SHOW_ACCURACY = True

TABLE_DATA = """
\\naive
model	verusbench (146)	dafnybench (67)	leetcode (28)	humaneval (68)
ds	88	49	3	8
gpt4o	63	55	3	6
qwen3-coder	101	60	2	13
o4-mini	101	55	4	14
sonnet-4.5	122	64	7	20

\\av
model	verusbench (146)	dafnybench (67)	leetcode (28)	humaneval (68)
ds	36	51	3	10
gpt4o	57	53	2	10
qwen3-coder	75	58	3	11
o4-mini	47	52	3	14
sonnet-4.5	110	64	4	19
total	146	67	28	68

\\tool
model	verusbench (146)	dafnybench (67)	leetcode (28)	humaneval (68)
ds	105	59	3	12
gpt4o	75	59	3	10
qwen3-coder	105	64	3	15
o4-mini	109	64	7	21
sonnet-4.5	129	64	8	28
"""

# Model name normalization for display
MODEL_NAME_MAP = {
    "ds": "DeepSeek-V3.1",
    "gpt4o": "GPT-4o",
    "o4-mini": "o4-mini",
    "qwen3-coder": "Qwen3-Coder",
    "sonnet-4.5": "Sonnet-4.5",
}

# Macros for dataset names in LaTeX header
DATASET_MACRO_MAP = {
    "verusbench": "\\verusbench",
    "dafnybench": "\\dafnybench",
    "leetcode": "\\lcbench",
    "humaneval": "\\humanevalbench",
}


def _split_columns(line: str):
    """
    Split a line into columns. Prefer tab-delimited; fallback to flexible whitespace.
    """
    if "\t" in line:
        parts = [p.strip() for p in line.split("\t")]
    else:
        parts = [p.strip() for p in re.split(r"\s+", line) if p.strip()]
    return [p for p in parts if p != ""]


def parse_table_data(raw: str):
    """
    Parse the block-form TABLE_DATA string into structured rows, dataset order, and totals.

    Returns:
        rows: List of tuples (method, model, values_list)
        dataset_order: List[str]
        dataset_totals: Dict[str, int]
    """
    rows = []
    dataset_order = []
    dataset_totals = {}

    current_method = None
    method_label_for_next_row = None
    header_parsed = False

    for raw_line in raw.strip().splitlines():
        line = raw_line.strip()
        if line == "":
            continue

        # Section/method marker starts with a backslash (e.g., \tool, \naive, \av)
        if line.startswith("\\") and line.lower() != "\\midrule":
            current_method = line
            method_label_for_next_row = current_method
            header_parsed = False
            continue

        cols = _split_columns(line)
        if not cols:
            continue

        # Header line begins with 'model'
        if cols[0].lower() == "model":
            dataset_order = []
            dataset_totals = {}
            for col in cols[1:]:
                m = re.match(r"(.+?)\s*\((\d+)\)$", col)
                if m:
                    name = m.group(1).strip()
                    total = int(m.group(2))
                    dataset_order.append(name)
                    dataset_totals[name] = total
                else:
                    name = col.strip()
                    dataset_order.append(name)
                    dataset_totals[name] = 0
            header_parsed = True
            continue

        # Totals line optionally appears at end
        if cols[0].lower() == "total" and dataset_order:
            for i, val in enumerate(cols[1:]):
                if i >= len(dataset_order):
                    break
                name = dataset_order[i]
                try:
                    parsed_val = int(val)
                except ValueError:
                    continue
                # Only fill if missing or zero
                if not dataset_totals.get(name):
                    dataset_totals[name] = parsed_val
            continue

        # Data row: model then values
        if header_parsed and dataset_order:
            raw_model = cols[0]
            model_key = raw_model.strip().lower()
            model_display = MODEL_NAME_MAP.get(model_key, raw_model)

            values = []
            for i, v in enumerate(cols[1:]):
                if i >= len(dataset_order):
                    break
                try:
                    values.append(int(v))
                except ValueError:
                    values.append(None)

            # Pad to match number of datasets if short
            if len(values) < len(dataset_order):
                values.extend([None] * (len(dataset_order) - len(values)))

            # Attach the current method to every data row for pivoting later
            rows.append(
                ((method_label_for_next_row or current_method), model_display, values)
            )
            method_label_for_next_row = None

    return rows, dataset_order, dataset_totals


def format_cell(value, total, include_accuracy=True):
    """
    Formats a single cell's content based on the include_accuracy flag.
    """
    if not isinstance(value, int):
        return ""

    if include_accuracy and total > 0:
        accuracy = (value / total) * 100
        # Show only percentage number (no % symbol), no absolute value
        return f"{accuracy:.1f}"
    else:
        return ""


def write_row(output: io.StringIO, cells: list[str]) -> None:
    """Write a LaTeX table row with correct line break."""
    output.write(" & ".join(cells) + " \\\\\n")


def generate_latex_table(include_accuracy=True):
    """
    Generates the full LaTeX table code from the parsed TABLE_DATA string.
    """
    output = io.StringIO()

    # Parse the block string into rows and metadata
    rows, dataset_order, dataset_totals = parse_table_data(TABLE_DATA)

    # Determine unique models and methods (tools) in order of appearance
    models_order = []
    methods_order = []
    for method, model, _ in rows:
        if model not in models_order:
            models_order.append(model)
        if method not in methods_order:
            methods_order.append(method)

    # Build lookup: (model, method) -> values list (per dataset index)
    lookup = {}
    for method, model, values in rows:
        key = (model, method)
        if key not in lookup:
            lookup[key] = values

    # Build column specification dynamically: title columns right, numbers left
    col_spec = "r|r|" + "|".join(["l"] * len(models_order))
    output.write("    \\setlength{\\tabcolsep}{5pt}\n")
    output.write("    \\renewcommand{\\arraystretch}{1.2}\n")
    output.write(f"    \\begin{{tabular}}{{{col_spec}}}\n")
    output.write("        \\toprule\n")

    # Header row: blank title columns, then model names
    header_top_parts = ["", ""]
    header_top_parts.extend([f"\\textbf{{{m}}}" for m in models_order])
    write_row(output, header_top_parts)

    output.write("        \\midrule\n")

    # Precompute max accuracy per (dataset, model) across techniques for bolding
    max_acc_by_dataset_model: dict[tuple[str, str], float | None] = {}
    for ds_index, ds_name in enumerate(dataset_order):
        totals = dataset_totals.get(ds_name, 0)
        for model in models_order:
            accs: list[float] = []
            for method in methods_order:
                vals = lookup.get((model, method))
                value = vals[ds_index] if vals and ds_index < len(vals) else None
                if isinstance(value, int) and totals > 0:
                    accs.append((value / totals) * 100.0)
            max_acc_by_dataset_model[(ds_name, model)] = max(accs) if accs else None

    # Precompute best baseline (\naive, \av) accuracy per (dataset, model)
    baseline_methods = {"\\naive", "\\av"}
    best_baseline_by_dataset_model: dict[tuple[str, str], float | None] = {}
    for ds_index, ds_name in enumerate(dataset_order):
        totals = dataset_totals.get(ds_name, 0)
        for model in models_order:
            accs: list[float] = []
            for method in methods_order:
                if method not in baseline_methods:
                    continue
                vals = lookup.get((model, method))
                value = vals[ds_index] if vals and ds_index < len(vals) else None
                if isinstance(value, int) and totals > 0:
                    accs.append((value / totals) * 100.0)
            best_baseline_by_dataset_model[(ds_name, model)] = (
                max(accs) if accs else None
            )

    # Body: one block per dataset, with prompting subrows
    for ds_index, ds_name in enumerate(dataset_order):
        ds_macro = DATASET_MACRO_MAP.get(ds_name, f"\\{ds_name}")
        totals = dataset_totals.get(ds_name, 0)
        for method_idx, method in enumerate(methods_order):
            row_parts = []
            if method_idx == 0:
                row_parts.append(
                    f"\\multirow{{{len(methods_order)}}}{{*}}{{\\bf {ds_macro}}}"
                )
            else:
                row_parts.append("")
            row_parts.append(f"\\textbf{{{method}}}" if method == "\\tool" else method)
            for model in models_order:
                vals = lookup.get((model, method))
                value = vals[ds_index] if vals and ds_index < len(vals) else None
                if isinstance(value, int) and totals > 0:
                    acc = (value / totals) * 100.0
                    cell = f"{acc:.1f}"
                    max_acc = max_acc_by_dataset_model.get((ds_name, model))

                    # Append relative improvement for \tool over best baseline
                    suffix = ""
                    if method == "\\tool":
                        best_baseline = best_baseline_by_dataset_model.get(
                            (ds_name, model)
                        )
                        if (
                            best_baseline is not None
                            and best_baseline > 0
                            and acc > best_baseline
                        ):
                            rel_improve = (acc - best_baseline) / best_baseline * 100.0
                            suffix = f" ($\\uparrow$ {rel_improve:.1f}\\%)"

                    is_best = max_acc is not None and abs(acc - max_acc) < 1e-9
                    if is_best:
                        cell = f"\\textbf{{{cell}{suffix}}}"
                        row_parts.append(cell)
                    else:
                        row_parts.append(cell + suffix)

                else:
                    row_parts.append("")
            write_row(output, row_parts)
        if ds_index < len(dataset_order) - 1:
            output.write("        \\midrule\n")

    output.write("        \\bottomrule\n")
    output.write("    \\end{tabular}\n")
    return output.getvalue()


if __name__ == "__main__":
    latex_code = generate_latex_table(include_accuracy=SHOW_ACCURACY)
    print(latex_code)
