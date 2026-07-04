from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

ROOT_DIR = Path(__file__).resolve().parent.parent
AUTOVERUS_CODE_DIR = ROOT_DIR / "verus-proof-synthesis" / "code"
if AUTOVERUS_CODE_DIR.is_dir() and str(AUTOVERUS_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOVERUS_CODE_DIR))

app = typer.Typer(help="ExVerus invariant generation and repair tools.", no_args_is_help=True)
assume_app = typer.Typer(help="Assume/assert conversion helpers.", no_args_is_help=True)
pipeline_app = typer.Typer(help="Invariant repair pipelines.", no_args_is_help=True)
app.add_typer(assume_app, name="assume")
app.add_typer(pipeline_app, name="pipeline")


def _print_check(name: str, ok: bool, detail: str) -> bool:
    typer.echo(f"{'ok' if ok else 'missing':7} {name}: {detail}")
    return ok


def _configured_verus_path() -> str | None:
    return os.environ.get("VERUS_PATH") or os.environ.get("VERUS_BIN") or shutil.which("verus")


def _check_verus(verus_path: str | None) -> tuple[bool, str]:
    if not verus_path:
        return False, "set VERUS_PATH, set VERUS_BIN, or add verus to PATH"
    result = subprocess.run([verus_path, "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        return True, result.stdout.splitlines()[0] if result.stdout else verus_path
    return False, (result.stderr or result.stdout).splitlines()[0]


@app.command()
def check(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit non-zero when a full pipeline dependency is missing.",
    ),
) -> None:
    """Check local files, toolchain paths, and LLM credentials."""
    verus_path = _configured_verus_path()
    verus_ok, verus_detail = _check_verus(verus_path)
    checks = [
        _print_check(
            "verus",
            verus_ok,
            verus_detail,
        ),
        _print_check(
            "autoverus code",
            (ROOT_DIR / "verus-proof-synthesis" / "code").is_dir(),
            str(ROOT_DIR / "verus-proof-synthesis" / "code"),
        ),
        _print_check(
            "prompts",
            (ROOT_DIR / "vinv" / "prompt").is_dir(),
            str(ROOT_DIR / "vinv" / "prompt"),
        ),
        _print_check(
            "rust converter",
            (ROOT_DIR / "tool" / "rs" / "convert" / "Cargo.toml").is_file(),
            str(ROOT_DIR / "tool" / "rs" / "convert"),
        ),
        _print_check(
            "llm key",
            any(os.environ.get(k) for k in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY")),
            "OPENAI_API_KEY, OPENROUTER_API_KEY, or ANTHROPIC_API_KEY",
        ),
    ]
    old_verus = os.environ.get("OLD_VERUS_PATH")
    _print_check("old verus", bool(old_verus), old_verus or "optional; needed only for --old-verus")
    if strict and not all(checks):
        raise typer.Exit(1)


@assume_app.command("convert")
def convert_assume(
    input_file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path | None = typer.Option(None, "--out", "-o", file_okay=False, help="Output directory."),
    use_assert: bool = typer.Option(False, "--use-assert", help="Emit asserts instead of assumes."),
) -> None:
    """Convert a Verus file into loop-harness assume/assert form."""
    from vinv.pipeline.assume.run_convert_assume_syn import convert_rust_file_to_file

    typer.echo(
        convert_rust_file_to_file(
            str(input_file),
            str(out) if out is not None else None,
            use_assert=use_assert,
        )
    )


@pipeline_app.command("repair")
def repair(
    task_type: str = typer.Option("ori", help="Pipeline task type."),
    model: str = typer.Option("deepseek-chat", help="LLM model id."),
    max_repair_attempts: int = typer.Option(10, help="Maximum repair attempts per proof."),
    cex_generation_strategy: str = typer.Option("simple", help="z3, simple, or verification."),
    cex_generalization_strategy: str = typer.Option("simple", help="simple or mut_val."),
    run_all: bool = typer.Option(False, help="Run all selected benchmark tasks."),
    num_cex: int = typer.Option(10, help="Counterexamples per repair attempt."),
    debug: bool = typer.Option(False, help="Use the debug result directory and task subset."),
    num_workers: int = typer.Option(1, help="Number of worker processes."),
    ablation: bool = typer.Option(False, help="Run the naive-repair ablation."),
    source: str = typer.Option("CLEANED_VB", help="CLEANED_VB, ADDITIONAL, THREEBENCH, or VSBHERB."),
) -> None:
    """Run the main ExVerus repair pipeline."""
    from vinv.pipeline.main import main as run_pipeline

    run_pipeline(
        task_type=task_type,
        model=model,
        max_repair_attempts=max_repair_attempts,
        cex_generation_strategy=cex_generation_strategy,
        cex_generalization_strategy=cex_generalization_strategy,
        run_all=run_all,
        num_cex=num_cex,
        debug=debug,
        num_workers=num_workers,
        ablation=ablation,
        source=source,
    )


@pipeline_app.command("one-step")
def one_step(
    model: str = typer.Option("gpt-4o", help="LLM model id."),
    max_repair_attempts: int = typer.Option(10, help="Maximum repair attempts per proof."),
    cex_generation_strategy: str = typer.Option("simple", help="z3, simple, or verification."),
    cex_generalization_strategy: str = typer.Option("simple", help="simple or mut_val."),
    num_cex: int = typer.Option(10, help="Counterexamples per repair attempt."),
    num_workers: int = typer.Option(1, help="Number of worker processes."),
    debug: bool = typer.Option(False, help="Use the debug result directory."),
    ablation: bool = typer.Option(False, help="Run the naive-repair ablation."),
    source: str = typer.Option("INJECTED", help="INJECTED or AV_TRAJ."),
) -> None:
    """Run repair on already generated almost-correct proofs."""
    from vinv.pipeline.one_step import main as run_one_step

    run_one_step(
        model=model,
        max_repair_attempts=max_repair_attempts,
        cex_generation_strategy=cex_generation_strategy,
        cex_generalization_strategy=cex_generalization_strategy,
        num_cex=num_cex,
        num_workers=num_workers,
        debug=debug,
        ablation=ablation,
        source=source,
    )


def main() -> None:
    app()
