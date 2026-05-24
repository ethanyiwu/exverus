import json
from enum import Enum
from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True)
analysis_app = typer.Typer(no_args_is_help=True)
assume_app = typer.Typer(no_args_is_help=True)
pipeline_app = typer.Typer(no_args_is_help=True)
app.add_typer(analysis_app, name="analysis")
app.add_typer(assume_app, name="assume")
app.add_typer(pipeline_app, name="pipeline")


class OutputFormat(str, Enum):
    text = "text"
    json = "json"


class PipelineTaskType(str, Enum):
    ori = "ori"
    obfs = "obfs"
    failed = "failed"


class PipelineSource(str, Enum):
    cleaned_vb = "CLEANED_VB"
    additional = "ADDITIONAL"
    threebench = "THREEBENCH"
    vsbherb = "VSBHERB"


class OneStepSource(str, Enum):
    av_traj = "AV_TRAJ"
    injected = "INJECTED"


class CexGenerationStrategy(str, Enum):
    z3 = "z3"
    simple = "simple"
    verification = "verification"


class CexGeneralizationStrategy(str, Enum):
    simple = "simple"
    mut_val = "mut_val"


class CexValidationBackend(str, Enum):
    legacy = "legacy"
    v2 = "v2"


def _write_output(payload: str, output: Path | None) -> None:
    if output is None:
        typer.echo(payload)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        payload if payload.endswith("\n") else f"{payload}\n",
        encoding="utf-8",
    )


def _load_assignments(
    assign_json: Path | None,
    assign: list[str] | None,
) -> dict[str, object]:
    assignments: dict[str, object] = {}
    if assign_json is not None:
        payload = json.loads(assign_json.read_text(encoding="utf-8"))
        if (
            isinstance(payload, dict)
            and "assignments" in payload
            and isinstance(payload["assignments"], dict)
        ):
            payload = payload["assignments"]
        if not isinstance(payload, dict):
            raise typer.BadParameter(
                "JSON must be an object mapping variable names to values.",
                param_hint="--assign-json",
            )
        assignments.update(payload)
    for item in assign or []:
        if "=" not in item:
            raise typer.BadParameter(
                f"Invalid assignment {item!r}; expected key=value.",
                param_hint="--assign",
            )
        key, value = item.split("=", 1)
        assignments[key.strip()] = value.strip()
    return assignments


def _render_pass_counts(json_path: Path, format: OutputFormat) -> str:
    from vinv.analysis.parse_pipeline_result import compute_pass_counts

    pass_counts, total_counts, total_pass, total_entries = compute_pass_counts(json_path)
    all_datasets = sorted(set(total_counts) | set(pass_counts))
    if format == OutputFormat.json:
        return json.dumps(
            {
                "json_path": str(json_path),
                "pass_counts": {dataset: pass_counts.get(dataset, 0) for dataset in all_datasets},
                "total_counts": {dataset: total_counts.get(dataset, 0) for dataset in all_datasets},
                "total_pass": total_pass,
                "total_entries": total_entries,
            },
            indent=2,
        )
    if not all_datasets:
        return f"No pass entries found or unrecognized JSON schema.\nScanned entries: {total_entries}"
    lines = ["Verification pass counts per sub-dataset:"]
    for dataset in all_datasets:
        lines.append(
            f"- {dataset}: {pass_counts.get(dataset, 0)} / {total_counts.get(dataset, 0)}"
        )
    lines.append(f"Total PASS: {total_pass} / {total_entries}")
    return "\n".join(lines)


@pipeline_app.command()
def run(
    task_type: PipelineTaskType = typer.Option(PipelineTaskType.ori, help="Task bucket metadata."),
    model: str = typer.Option("deepseek-chat", help="LLM model to use."),
    max_repair_attempts: int = typer.Option(10, min=1, help="Maximum repair attempts per proof."),
    cex_generation_strategy: CexGenerationStrategy = typer.Option(
        CexGenerationStrategy.simple,
        help="Counterexample generation strategy.",
    ),
    cex_generalization_strategy: CexGeneralizationStrategy = typer.Option(
        CexGeneralizationStrategy.simple,
        help="Counterexample generalization strategy.",
    ),
    cex_validation_backend: CexValidationBackend = typer.Option(
        CexValidationBackend.v2,
        help="Counterexample validation backend.",
    ),
    run_all: bool = typer.Option(False, help="Process the full benchmark set."),
    num_cex: int = typer.Option(10, min=1, help="Maximum number of CEXs to keep."),
    debug: bool = typer.Option(False, help="Write outputs under pipeline_debug."),
    num_workers: int = typer.Option(1, min=1, help="Parallel worker count."),
    ablation: bool = typer.Option(False, help="Use naive repair instead of CEX repair."),
    source: PipelineSource = typer.Option(
        PipelineSource.cleaned_vb,
        help="Benchmark source to process.",
    ),
) -> None:
    from vinv.pipeline.main import main as pipeline_main

    pipeline_main(
        task_type=task_type.value,
        model=model,
        max_repair_attempts=max_repair_attempts,
        cex_generation_strategy=cex_generation_strategy.value,
        cex_generalization_strategy=cex_generalization_strategy.value,
        cex_validation_backend=cex_validation_backend.value,
        run_all=run_all,
        num_cex=num_cex,
        debug=debug,
        num_workers=num_workers,
        ablation=ablation,
        source=source.value,
    )


@pipeline_app.command("one-step")
def one_step(
    model: str = typer.Option("gpt-4o", help="LLM model to use."),
    max_repair_attempts: int = typer.Option(10, min=1, help="Maximum repair attempts per proof."),
    cex_generation_strategy: CexGenerationStrategy = typer.Option(
        CexGenerationStrategy.simple,
        help="Counterexample generation strategy.",
    ),
    cex_generalization_strategy: CexGeneralizationStrategy = typer.Option(
        CexGeneralizationStrategy.simple,
        help="Counterexample generalization strategy.",
    ),
    cex_validation_backend: CexValidationBackend = typer.Option(
        CexValidationBackend.v2,
        help="Counterexample validation backend.",
    ),
    num_cex: int = typer.Option(10, min=1, help="Maximum number of CEXs to keep."),
    num_workers: int = typer.Option(1, min=1, help="Parallel worker count."),
    debug: bool = typer.Option(False, help="Write outputs under pipeline_debug."),
    ablation: bool = typer.Option(False, help="Use naive repair instead of CEX repair."),
    source: OneStepSource = typer.Option(
        OneStepSource.injected,
        help="One-step dataset source.",
    ),
) -> None:
    from vinv.pipeline.one_step import main as one_step_main

    one_step_main(
        model=model,
        max_repair_attempts=max_repair_attempts,
        cex_generation_strategy=cex_generation_strategy.value,
        cex_generalization_strategy=cex_generalization_strategy.value,
        cex_validation_backend=cex_validation_backend.value,
        num_cex=num_cex,
        num_workers=num_workers,
        debug=debug,
        ablation=ablation,
        source=source.value,
    )


@assume_app.command()
def convert(
    input_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Input Rust file."),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="Directory for converted output."),
    use_assert: bool = typer.Option(False, help="Use assert instead of assume at loop heads."),
    print_output: bool = typer.Option(True, "--print/--no-print", help="Print converted code when no output directory is given."),
) -> None:
    from vinv.pipeline.assume.run_convert_assume_syn import (
        convert_rust_file_to_file,
        convert_rust_file_to_string,
    )

    if output_dir is not None:
        typer.echo(
            convert_rust_file_to_file(
                str(input_path),
                str(output_dir),
                use_assert,
            )
        )
        return
    converted = convert_rust_file_to_string(str(input_path), use_assert)
    if print_output:
        typer.echo(converted)


@assume_app.command("validate-cex")
def validate_cex(
    converted: Path = typer.Argument(..., exists=True, dir_okay=False, help="Converted Rust file to validate."),
    assign_json: Path | None = typer.Option(
        None,
        "--assign-json",
        exists=True,
        dir_okay=False,
        help="JSON file containing assignments.",
    ),
    assign: list[str] | None = typer.Option(
        None,
        "--assign",
        help="Inline assignment in key=value form. Repeat as needed.",
    ),
    work_dir: Path | None = typer.Option(None, "--work-dir", help="Directory for artifacts."),
    old_verus: bool = typer.Option(False, "--old-verus", help="Use OLD_VERUS_PATH instead of VERUS_PATH."),
) -> None:
    from vinv.pipeline.assume.cex_validator import validate_cex_on_file

    assignments = _load_assignments(assign_json, assign)
    if not assignments:
        raise typer.BadParameter(
            "Provide at least one assignment via --assign-json or --assign.",
        )
    typer.echo(
        json.dumps(
            validate_cex_on_file(
                converted,
                assignments,
                work_dir=work_dir,
                use_old_verus=old_verus,
            ),
            indent=2,
        )
    )


@analysis_app.command("parse-pipeline")
def parse_pipeline(
    json_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Pipeline result JSON file."),
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
    output: Path | None = typer.Option(None, "--output", help="Write output to a file instead of stdout."),
) -> None:
    _write_output(_render_pass_counts(json_path, format), output)


@analysis_app.command("run-error-stats")
def run_error_stats(
    root: Path = typer.Argument(..., exists=True, help="Root directory to scan."),
    strategy: str = typer.Option(..., help="Strategy directory name to inspect."),
    gen_id: str = typer.Option("gen_0", help="Generation directory name."),
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
    top: int | None = typer.Option(None, min=1, help="Only keep the top N rows."),
    markdown_table: bool = typer.Option(False, help="Render text output as a Markdown table."),
    output: Path | None = typer.Option(None, "--output", help="Write output to a file instead of stdout."),
) -> None:
    from vinv.analysis.run_error_stats import (
        collect_run_error_stats,
        render_markdown_report,
        render_text_report,
    )

    if format == OutputFormat.json and markdown_table:
        raise typer.BadParameter("--markdown-table requires --format text.")
    stats = collect_run_error_stats(root=root, strategy=strategy, gen_id=gen_id)
    if format == OutputFormat.json:
        payload = json.dumps(stats, indent=2)
    elif markdown_table:
        payload = render_markdown_report(stats, top=top)
    else:
        payload = render_text_report(stats, top=top)
    _write_output(payload, output)


@analysis_app.command("cex-validation-stats")
def cex_validation_stats(
    root: Path = typer.Argument(..., exists=True, help="Root directory to scan."),
    strategy: str = typer.Option(..., help="Strategy directory name to inspect."),
    gen_id: str = typer.Option("gen_0", help="Generation directory name."),
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
    include_steps: bool = typer.Option(False, help="Include per-step records in JSON output."),
    print_all_failed_try_dirs: bool = typer.Option(
        False,
        help="Include try_dir paths for steps where every CEX validation failed.",
    ),
    output: Path | None = typer.Option(None, "--output", help="Write output to a file instead of stdout."),
) -> None:
    from vinv.analysis.cex_validation_stats import (
        collect_cex_validation_stats,
        render_text_report,
    )

    stats = collect_cex_validation_stats(
        root=root,
        strategy=strategy,
        gen_id=gen_id,
        include_steps=include_steps,
        include_all_failed_try_dirs=print_all_failed_try_dirs,
    )
    payload = json.dumps(stats, indent=2) if format == OutputFormat.json else render_text_report(stats)
    _write_output(payload, output)


@analysis_app.command("autoverus-lynette-recalc")
def autoverus_lynette_recalc(
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
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
    include_repairs: bool = typer.Option(
        True, "--repairs/--no-repairs", help="Include verified repair candidates."
    ),
    examples: int = typer.Option(
        12, min=0, help="Number of safe repair examples in text output."
    ),
    output: Path | None = typer.Option(
        None, "--output", help="Write JSON report to a file."
    ),
) -> None:
    from vinv.analysis.autoverus_lynette_recalc import (
        collect_recalculated_stats,
        render_text,
    )

    report = collect_recalculated_stats(run_dir, lynette_bin, include_repairs)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _write_output(
        (
            json.dumps(report, indent=2)
            if format == OutputFormat.json
            else render_text(report, examples)
        ),
        None,
    )


@analysis_app.command("one-step-cex")
def one_step_cex(
    try_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Single try_* directory."),
    output: Path | None = typer.Option(None, "--output", help="Write summary JSON to a file."),
    quiet: bool = typer.Option(False, help="Suppress stdout JSON output."),
) -> None:
    from vinv.analysis.one_step_cex import analyze_try_dir

    analyze_try_dir(
        str(try_dir),
        out=str(output) if output is not None else None,
        quiet=quiet,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
