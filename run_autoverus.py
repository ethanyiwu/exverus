from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

from vinv.autoverus import (
    AUTOVERUS_RUNS_DIR,
    AUTOVERUS_TOOL_DIR,
    AutoVerusConfig,
    build_autoverus_output_dir,
    parse_phase1_examples,
    render_autoverus_summary,
    resolve_autoverus_config_file,
    resolve_autoverus_input_dirs,
    run_autoverus,
)

app = typer.Typer(no_args_is_help=True)


class AutoVerusSource(str, Enum):
    vb = "vb"
    cleaned_vb = "cleaned_vb"
    additional = "additional"
    threebench = "threebench"
    vsbherb = "vsbherb"


@app.callback(invoke_without_command=True)
def main(
    source: AutoVerusSource = typer.Option(
        AutoVerusSource.cleaned_vb,
        help="Benchmark collection that provides the unverified inputs.",
    ),
    model: str = typer.Option(
        "gpt-4o",
        help="Model id used to select the default AutoVerus config.",
    ),
    name: str | None = typer.Option(
        None,
        help="Experiment label. Defaults to <model>-<source>.",
    ),
    suite_root: Path | None = typer.Option(
        None,
        "--suite-root",
        exists=True,
        file_okay=False,
        help="Override the benchmark suite root with benchmark-named subdirectories.",
    ),
    config_file: Path | None = typer.Option(
        None,
        "--config-file",
        exists=True,
        dir_okay=False,
        help="Override the AutoVerus config file.",
    ),
    tool_dir: Path | None = typer.Option(
        None,
        "--tool-dir",
        exists=True,
        file_okay=False,
        help="Path to the AutoVerus checkout.",
    ),
    output_root: Path | None = typer.Option(
        None,
        "--output-root",
        help="Root directory for dated AutoVerus runs.",
    ),
    temp: float = typer.Option(1.0, help="LLM temperature."),
    disable_safe: bool = typer.Option(
        False,
        help="Disable the AutoVerus safe-code guard.",
    ),
    repair_uniform: bool = typer.Option(
        False,
        help="Use uniform repair ordering.",
    ),
    phase1_examples: str = typer.Option(
        "3,6,7",
        help="Comma- or space-separated phase-1 example ids.",
    ),
    repair_num: int = typer.Option(
        10,
        min=1,
        help="Maximum repair attempts per file.",
    ),
    phase_uniform: bool = typer.Option(False, help="Unify the first two phases."),
    disable_ranking: bool = typer.Option(
        False,
        help="Disable candidate ranking.",
    ),
    direct_repair: bool = typer.Option(False, help="Run direct repair."),
    disable_one_refinement: int = typer.Option(
        -1,
        help="Disable one refinement index.",
    ),
    is_baseline: bool = typer.Option(
        False,
        help="Run the baseline generation mode.",
    ),
    num_workers: int = typer.Option(1, min=1, help="Parallel worker count."),
    rerun: bool = typer.Option(
        False,
        help="Re-run files even if an output already exists.",
    ),
) -> None:
    resolved_tool_dir = tool_dir or AUTOVERUS_TOOL_DIR
    resolved_output_root = output_root or AUTOVERUS_RUNS_DIR
    try:
        resolved_input_dirs = resolve_autoverus_input_dirs(
            source=source.value,
            suite_root=suite_root,
        )
    except ValueError as exc:
        raise typer.BadParameter(
            str(exc),
            param_hint="--suite-root",
        ) from exc
    try:
        resolved_phase1_examples = parse_phase1_examples(phase1_examples)
    except ValueError as exc:
        raise typer.BadParameter(
            str(exc),
            param_hint="--phase1-examples",
        ) from exc
    resolved_name = name or f"{model}-{source.value}"
    summary = run_autoverus(
        AutoVerusConfig(
            input_dirs=resolved_input_dirs,
            output_dir=build_autoverus_output_dir(
                output_root=resolved_output_root,
                name=resolved_name,
                temp=temp,
            ),
            tool_dir=resolved_tool_dir,
            config_file=resolve_autoverus_config_file(
                model=model,
                config_file=config_file,
            ),
            temp=temp,
            phase1_examples=resolved_phase1_examples,
            repair_num=repair_num,
            disable_safe=disable_safe,
            repair_uniform=repair_uniform,
            phase_uniform=phase_uniform,
            disable_ranking=disable_ranking,
            direct_repair=direct_repair,
            disable_one_refinement=disable_one_refinement,
            is_baseline=is_baseline,
            num_workers=num_workers,
            rerun=rerun,
        )
    )
    typer.echo(render_autoverus_summary(summary))


if __name__ == "__main__":
    app()
