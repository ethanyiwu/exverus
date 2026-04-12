import io
import re

# --- Hyperparameter ---
# Set this to False if you only want to see the verified number (e.g., 112)
# and not the accuracy percentage (e.g., 112 / 76.7%).
SHOW_ACCURACY = True

TABLE_DATA = """
\\tool
	model	\\naive	\\toolsimplegenz	\\tool
\\verusbench (146)	ds	88	94	105
	gpt4o	63	68	75
	qwen3-coder	101	96	105
	o4-mini	101	100	109
	sonnet-4.5	122	124	129
\\dafnybench (67)	ds	49	59	59
	gpt4o	55	60	59
	qwen3-coder	55	62	64
	o4-mini	60	57	64
	sonnet-4.5	64	64	64
\\lcbench (28)	ds	3	2	3
	gpt4o	3	3	3
	qwen3-coder	4	3	3
	o4-mini	2	5	7
	sonnet-4.5	7	6	8
\\humanevalbench (68)	ds	8	12	12
	gpt4o	6	6	10
	qwen3-coder	14	13	15
	o4-mini	13	15	21
	sonnet-4.5	20	20	28
\\obfsbench (266)	ds	163	174	217
	gpt4o	76	94	109
	qwen3-coder	190	191	204
	o4-mini	186	194	212
	sonnet-4.5	231	228	241
"""

# Model name normalization for display
MODEL_NAME_MAP = {
    "ds": "DeepSeek-V3.1",
    "gpt4o": "GPT-4o",
    "o4-mini": "o4-mini",
    "qwen3-coder": "Qwen3-Coder",
    "sonnet-4.5": "Sonnet-4.5",
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
    Parse the ablation TABLE_DATA format into structured rows, dataset order, and totals.

    Expected format:
        \\tool
            model    <tool1>    <tool2>    ...
        \\datasetA (N)
            <modelA>  v11  v12 ...
            <modelB>  v21  v22 ...
        \\datasetB (M)
            ...

    Returns:
        rows: List of tuples (method, model, values_list) with values aligned to dataset_order
        dataset_order: List[str]
        dataset_totals: Dict[str, int]
    """
    dataset_order: list[str] = []
    dataset_totals: dict[str, int] = {}
    methods_order: list[str] = []
    models_order: list[str] = []

    # (model_display, method_label) -> list of values per dataset index
    values_by_model_method: dict[tuple[str, str], list] = {}

    in_tools_header = False
    current_dataset = None
    current_dataset_index = -1

    for raw_line in raw.strip().splitlines():
        line = raw_line.strip()
        if line == "":
            continue

        # Section markers
        if line.startswith("\\"):
            if line.lower() == "\\tool":
                in_tools_header = True
                continue

            # Dataset header like: \verusbench (146) [optional inline first row]
            m = re.match(r"\\([^\\()]+)\s*(?:\((\d+)\))?", line)
            if m:
                current_dataset = m.group(1).strip()
                total = int(m.group(2)) if m.group(2) is not None else 0
                dataset_order.append(current_dataset)
                dataset_totals[current_dataset] = total
                current_dataset_index = len(dataset_order) - 1
                in_tools_header = False

                # Handle optional inline first data row after the dataset header
                remainder = line[m.end() :].strip()
                if remainder:
                    inline_cols = _split_columns(remainder)
                    if inline_cols:
                        raw_model = inline_cols[0]
                        model_key = raw_model.strip().lower()
                        model_display = MODEL_NAME_MAP.get(model_key, raw_model)
                        if model_display not in models_order:
                            models_order.append(model_display)
                        for method_idx, method_label in enumerate(methods_order):
                            key = (model_display, method_label)
                            if key not in values_by_model_method:
                                values_by_model_method[key] = []
                            while len(values_by_model_method[key]) < len(dataset_order):
                                values_by_model_method[key].append(None)
                            value_token = (
                                inline_cols[1 + method_idx]
                                if 1 + method_idx < len(inline_cols)
                                else ""
                            )
                            try:
                                parsed_value = int(value_token)
                            except ValueError:
                                parsed_value = None
                            values_by_model_method[key][
                                current_dataset_index
                            ] = parsed_value

                continue

        cols = _split_columns(line)
        if not cols:
            continue

        # Tools header row: starts with 'model' then tool names
        if in_tools_header and cols[0].lower() == "model":
            methods_order = cols[1:]
            in_tools_header = False
            continue

        # Data row under a dataset: <model> then values for each tool
        if current_dataset is not None and cols:
            raw_model = cols[0]
            model_key = raw_model.strip().lower()
            model_display = MODEL_NAME_MAP.get(model_key, raw_model)
            if model_display not in models_order:
                models_order.append(model_display)

            # Ensure values list exists and has correct length for each method
            for method_idx, method_label in enumerate(methods_order):
                key = (model_display, method_label)
                if key not in values_by_model_method:
                    values_by_model_method[key] = []
                # Extend to current dataset index
                while len(values_by_model_method[key]) < len(dataset_order):
                    values_by_model_method[key].append(None)
                # Parse value for this dataset+method
                value_token = cols[1 + method_idx] if 1 + method_idx < len(cols) else ""
                try:
                    parsed_value = int(value_token)
                except ValueError:
                    parsed_value = None
                values_by_model_method[key][current_dataset_index] = parsed_value

    # Build rows in stable order: models outer, methods inner
    rows: list[tuple[str, str, list]] = []
    for model in models_order:
        for method in methods_order:
            key = (model, method)
            values = values_by_model_method.get(key, [None] * len(dataset_order))
            # Pad to ensure length matches number of datasets
            if len(values) < len(dataset_order):
                values = values + [None] * (len(dataset_order) - len(values))
            rows.append((method, model, values))

    return rows, dataset_order, dataset_totals


def format_cell(value, total, include_accuracy=True):
    """
    Formats a single cell's content based on the include_accuracy flag.
    """
    if not isinstance(value, int):
        return ""

    if include_accuracy and total > 0:
        accuracy = (value / total) * 100
        return f"{value} ({accuracy:.1f}\\%)"
    else:
        return str(value)


def _sanitize_latex_header(label: str) -> str:
    """
    Sanitize header labels for LaTeX tabular cells.
    - If the label starts with a backslash (e.g., \tool), render it literally.
    """
    if not isinstance(label, str):
        return label
    label = label.strip()
    if label.startswith("\\"):
        # Render a literal backslash + command name in monospaced
        return f"\\texttt{{\\textbackslash {label[1:]}}}"
    return label


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

    # Build column specification dynamically: Dataset, Technique, then models
    # Title columns right-aligned, numbers left-aligned
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
        total = dataset_totals.get(ds_name, 0)
        for model in models_order:
            accs: list[float] = []
            for method in methods_order:
                vals = lookup.get((model, method))
                value = vals[ds_index] if vals and ds_index < len(vals) else None
                if isinstance(value, int) and total > 0:
                    accs.append((value / total) * 100.0)
            max_acc_by_dataset_model[(ds_name, model)] = max(accs) if accs else None

    # Precompute best baseline (\naive, \av, \toolsimplegenz) accuracy per (dataset, model)
    baseline_methods = {"\\naive", "\\av", "\\toolsimplegenz"}
    best_baseline_by_dataset_model: dict[tuple[str, str], float | None] = {}
    for ds_index, ds_name in enumerate(dataset_order):
        total = dataset_totals.get(ds_name, 0)
        for model in models_order:
            accs: list[float] = []
            for method in methods_order:
                if method not in baseline_methods:
                    continue
                vals = lookup.get((model, method))
                value = vals[ds_index] if vals and ds_index < len(vals) else None
                if isinstance(value, int) and total > 0:
                    accs.append((value / total) * 100.0)
            best_baseline_by_dataset_model[(ds_name, model)] = (
                max(accs) if accs else None
            )

    # Body: one block per dataset, with technique subrows
    for ds_index, ds_name in enumerate(dataset_order):
        total = dataset_totals.get(ds_name, 0)
        for method_idx, method in enumerate(methods_order):
            row_parts = []
            if method_idx == 0:
                row_parts.append(
                    f"\\multirow{{{len(methods_order)}}}{{*}}{{\\bf \\{ds_name}}}"
                )
            else:
                row_parts.append("")
            row_parts.append(f"\\textbf{{{method}}}" if method == "\\tool" else method)
            for model in models_order:
                vals = lookup.get((model, method))
                value = vals[ds_index] if vals and ds_index < len(vals) else None
                if isinstance(value, int) and total > 0:
                    acc = (value / total) * 100.0
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
                        row_parts.append(f"\\textbf{{{cell}{suffix}}}")
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
