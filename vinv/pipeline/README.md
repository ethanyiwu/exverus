# Pipeline for proof generation/repair

The project now exposes a single CLI entrypoint:

```bash
uv sync
uv run vinv --help
```

## Main commands

Run the full repair pipeline:

```bash
uv run vinv pipeline run --model deepseek-chat --source CLEANED_VB --run-all
```

Run the one-step repair pipeline:

```bash
uv run vinv pipeline one-step --model gpt-4o --source INJECTED
```

Convert a proof into assume/assert form:

```bash
uv run vinv assume convert path/to/input.rs --output-dir path/to/out
```

Validate a counterexample against converted code:

```bash
uv run vinv assume validate-cex path/to/converted.rs --assign x=1 --assign y=2
```

Parse aggregated pipeline results:

```bash
uv run vinv analysis parse-pipeline results/pipeline/gpt-4o/CLEANED_VB/global_repair_status_z3_mut_val_10.json
```

Summarize run-level error statistics:

```bash
uv run vinv analysis run-error-stats results/pipeline/gpt-4o/CLEANED_VB --strategy cex_repair_z3_mut_val_10
```

Summarize CEX validation behavior:

```bash
uv run vinv analysis cex-validation-stats results/pipeline/gpt-4o/CLEANED_VB --strategy cex_repair_z3_mut_val_10
```

Inspect one repaired attempt directory:

```bash
uv run vinv analysis one-step-cex results/pipeline/gpt-4o/CLEANED_VB/some_task/cex_repair_z3_mut_val_10/gen_0/try_1
```

## Key idea

1. Generate a candidate repair from a failing proof.
2. Use counterexamples to distinguish weak invariants from wrong invariants.
3. Generalize useful counterexamples into stronger repairs and iterate.

## Notes

- The unified CLI is a thin layer over the existing pipeline and analysis modules.
- Existing module entrypoints still work, but the recommended interface is `uv run vinv ...`.
