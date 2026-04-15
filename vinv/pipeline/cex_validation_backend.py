from __future__ import annotations

from pathlib import Path
from typing import Literal

from vinv.pipeline.cex_harness_v2 import (
    load_extracted_harness_v2,
    prepare_extracted_harness_v2,
)
from vinv.pipeline.parser_utils import extract_loop_for_error
from vinv.pipeline.validator_extracted import (
    validate_blocking_list_extracted,
    validate_cex_list_extracted,
)
from vinv.pipeline.validator_extracted_v2 import (
    normalize_counterexample_v2,
    validate_blocking_list_extracted_v2,
    validate_cex_list_extracted_v2,
)

CexValidationBackend = Literal["legacy", "v2"]


def prepare_extracted_harness(
    proof_file: Path,
    verus_error: object,
    out_path: Path,
    backend: CexValidationBackend = "v2",
) -> Path:
    if backend == "v2":
        prepare_extracted_harness_v2(proof_file, verus_error, out_path)
        return out_path
    if not out_path.exists():
        ok = extract_loop_for_error(proof_file, verus_error, out_path)
        if not ok:
            raise ValueError(f"Failed to extract loop harness for {proof_file}")
    return out_path


def validate_cex_list_with_backend(
    extracted_file: Path,
    counter_examples: list[CounterExample],
    validation_dir: Path,
    backend: CexValidationBackend = "v2",
) -> list[dict[str, object]]:
    if backend == "v2":
        return validate_cex_list_extracted_v2(
            extracted_file=extracted_file,
            counter_examples=counter_examples,
            validation_dir=validation_dir,
        )
    return validate_cex_list_extracted(
        extracted_file=extracted_file,
        counter_examples=counter_examples,
        validation_dir=validation_dir,
    )


def validate_blocking_list_with_backend(
    repaired_extracted_file: Path,
    counter_examples: list[CounterExample],
    validation_dir: Path,
    baseline_regions: dict[int, str | None] | None = None,
    baseline_results_path: Path | None = None,
    backend: CexValidationBackend = "v2",
) -> list[dict[str, object]]:
    if backend == "v2":
        return validate_blocking_list_extracted_v2(
            repaired_extracted_file=repaired_extracted_file,
            counter_examples=counter_examples,
            validation_dir=validation_dir,
            baseline_regions=baseline_regions,
            baseline_results_path=baseline_results_path,
        )
    return validate_blocking_list_extracted(
        repaired_extracted_file=repaired_extracted_file,
        counter_examples=counter_examples,
        validation_dir=validation_dir,
        baseline_results_path=baseline_results_path,
    )


def canonicalize_generated_cex_results(
    results: list[object],
    extracted_file: Path | None,
    backend: CexValidationBackend = "v2",
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if backend != "v2" or extracted_file is None or not extracted_file.exists():
        cleaned = [dict(item) for item in results if isinstance(item, dict)]
        diagnostics = [
            {
                "index": idx,
                "kept": isinstance(item, dict),
                "reason": "non_dict_result" if not isinstance(item, dict) else "legacy_passthrough",
            }
            for idx, item in enumerate(results)
        ]
        return cleaned, diagnostics

    harness = load_extracted_harness_v2(extracted_file)
    cleaned: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    for idx, item in enumerate(results):
        if not isinstance(item, dict):
            diagnostics.append(
                {"index": idx, "kept": False, "reason": "non_dict_result"}
            )
            continue
        normalized = normalize_counterexample_v2(item, harness)
        state = dict(normalized.injected_assignments)
        state.update(normalized.post_state_hints)
        kept = bool(normalized.injected_assignments)
        diagnostics.append(
            {
                "index": idx,
                "kept": kept,
                "reason": "ok" if kept else "no_injectable_assignments",
                "canonical_state": state,
                "injected_names": sorted(normalized.injected_assignments),
                "post_state_hints": normalized.post_state_hints,
                "alias_map": normalized.alias_map,
                "dropped_keys": normalized.dropped_keys,
            }
        )
        if kept:
            cleaned.append(state)
    return cleaned, diagnostics


__all__ = [
    "CexValidationBackend",
    "canonicalize_generated_cex_results",
    "prepare_extracted_harness",
    "validate_blocking_list_with_backend",
    "validate_cex_list_with_backend",
]
