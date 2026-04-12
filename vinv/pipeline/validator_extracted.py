#!/usr/bin/env python3
"""
Validate a counterexample (CEX) on an extracted while-loop harness.

Inputs:
- extracted_file: the extracted harness file (Path) with region markers
- cex_assignments: dict mapping var -> concrete value (Rust syntax strings preferred)

Behavior:
- Inject assignments into the extracted harness right after the
  "// before loop body START" marker.
- Run Verus on the injected program and determine if an assertion failure is detected.
- If an assertion fails, classify the failure region as one of:
  { "before", "after", "neither" } based on marker ranges.
  If no region markers are present (base-case mode), any assertion failure is
  classified as "before".

Outputs (dict):
- verification_passed (bool): True if Verus reports no verification errors
- detected (bool): True if an assertion failure is detected (i.e., real CEX)
- failure_region (str | None): "before" | "after" | "neither" when detected else None
- injected_file (str): path to the injected file for inspection
- errors (list[str]): list of error type names reported by Verus
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from veval import VerusErrorType, VEval

from vinv.pipeline.assume.inject_extracted import inject_into_extracted_code
from vinv.pipeline.counter_example import CounterExample
from vinv.verus_utils import verus_format


def _to_verus_expr(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, (list, tuple)):
        inner = ", ".join(_to_verus_expr(x) for x in v)
        return f"({inner})"
    return str(v)


def _classify_failure_region(
    injected_code: str, assert_fail_lines: list[int]
) -> tuple[Optional[str], bool]:
    """Return (region, both_regions_flag).

    region is one of: "before" | "after" | "neither" | None based on marker ranges.
    Precedence: if any failure is in the BEFORE region, return "before"; else if any in AFTER, return "after"; else "neither" if there are failures outside markers, otherwise None.
    both_regions_flag is True if failures are found in both before and after regions.
    """
    lines = injected_code.splitlines()
    before_start = None
    before_end = None
    after_start = None
    after_end = None

    # find the region markers (inductiveness mode)
    for idx, line in enumerate(lines, start=1):
        s = line.strip()
        if s == "// before loop body START":
            before_start = idx
        elif s == "// before loop body END":
            before_end = idx
        elif s == "// after loop body START":
            after_start = idx
        elif s == "// after loop body END":
            after_end = idx

    # Base-case fallback: if no markers present (base-case mode), treat any failure as BEFORE
    if (
        before_start is None
        and before_end is None
        and after_start is None
        and after_end is None
    ):
        return ("before" if assert_fail_lines else None), False

    def in_range(lno: int, start: Optional[int], end: Optional[int]) -> bool:
        return start is not None and end is not None and start < lno < end

    sorted_lines = sorted(set(assert_fail_lines))
    has_before = any(in_range(lno, before_start, before_end) for lno in sorted_lines)
    has_after = any(in_range(lno, after_start, after_end) for lno in sorted_lines)

    if has_before and has_after:
        return "before", True  # prefer "before" but signal both
    if has_before:
        return "before", False
    if has_after:
        return "after", False

    # Fallbacks when markers exist but strict in-range check misses (e.g., formatting/line shifts)
    if sorted_lines:
        # Inclusive boundary check
        if before_start is not None and before_end is not None:
            if any((before_start <= lno <= before_end) for lno in sorted_lines):
                return "before", False
        if after_start is not None and after_end is not None:
            if any((after_start <= lno <= after_end) for lno in sorted_lines):
                return "after", False
        # Heuristic: if any failure occurs before the AFTER region begins, call it BEFORE
        if after_start is not None and any(lno < after_start for lno in sorted_lines):
            return "before", False
        # Otherwise, if we have a BEFORE region marker at all, prefer classifying as BEFORE
        if before_start is not None:
            return "before", False

    return ("neither" if sorted_lines else None), False


def _is_blocked(
    orig_region: Optional[str], mut_detected: bool, mut_region: Optional[str]
) -> bool:
    """
    Comparative blocking rule per CEX:
      - If original failure was BEFORE the loop body, the mutant should eliminate
        the failure entirely (no AssertFail anywhere).
      - If original failure was AFTER the loop body, the mutant should either move
        the failure to BEFORE (i.e., invariants/prior facts fail) or eliminate it.
      - Otherwise (None/"neither"/unknown), treat as not blocked.
    """
    if orig_region == "before":
        return not mut_detected
    if orig_region == "after":
        return (mut_detected and mut_region == "before") or (not mut_detected)
    return False


def _load_baseline_regions(batch_results_path: Path) -> Dict[int, Optional[str]]:
    """
    Read base harness results (batch_results.json) to map cex_index -> failure_region.
    Unknowns or missing indices map to None.
    """
    data = json.loads(Path(batch_results_path).read_text(encoding="utf-8"))
    mapping: Dict[int, Optional[str]] = {}
    for item in data:
        idx = item.get("cex_index")
        reg = item.get("failure_region")
        if isinstance(idx, int):
            mapping[idx] = reg if isinstance(reg, str) else None
    return mapping


def validate_extracted_cex(
    extracted_file: Path,
    cex_assignments: Dict[str, object],
    cex_dir: Path,
    cex_index: str,
    cex_obj: CounterExample,
) -> Dict[str, object]:
    cex_dir.mkdir(parents=True, exist_ok=True)

    # 1) Read extracted harness and inject assignments
    # Pass raw values; injector will render correctly-typed expressions using type info
    injected_file = cex_dir / "injected_cex.rs"
    inject_into_extracted_code(cex_dir, extracted_file, injected_file, cex_assignments)

    # Determine ID for this injection to avoid overwrites (use index if provided)
    try:
        verus_format(injected_file)
    except Exception:
        logger.error(f"Failed to format injected code: {injected_file}")
        pass

    # 2) Run Verus via VEval on the injected file contents
    v = VEval(injected_file.read_text(encoding="utf-8"), logger)
    v.eval_and_get_score(max_errs=10, json_mode=True)

    errors = v.get_errors()
    verification_passed = (errors == 0) and (not v.compilation_error)

    if v.compilation_error:
        logger.error(f"Compilation error for injected code: {injected_file}")

    # Gather assertion failures and their line numbers
    assert_fail_lines: list[int] = []
    detected = False
    error_names: list[str] = []

    for e in v.get_failures():
        error_names.append(e.error.name)
        if e.error == VerusErrorType.AssertFail:
            detected = True
            for t in e.trace:
                (ls, _le) = t.get_lines()
                if isinstance(ls, int) and ls > 0:
                    assert_fail_lines.append(ls)

    # Classify failure region (with base-case fallback). If compilation error occurred,
    # do not consider it validated: treat as no detection and no region.
    if v.compilation_error:
        failure_region, both_regions = (None, False)
        detected = False
        if "CompilationError" not in error_names:
            error_names.append("CompilationError")
    else:
        failure_region, both_regions = _classify_failure_region(
            injected_file.read_text(encoding="utf-8"), assert_fail_lines
        )
    warning: Optional[str] = None
    if both_regions:
        warning = f"Assertion failures detected in BOTH before and after loop body regions; prioritizing 'before' for {injected_file}"
        logger.warning(warning)

    result = {
        "verification_passed": verification_passed,
        "detected": detected and not verification_passed,
        "failure_region": failure_region,
        "injected_file": str(injected_file),
        "errors": error_names,
        "cex_index": cex_index,
        "compilation_error": bool(v.compilation_error),
    }
    if cex_obj is not None:
        try:
            # Prefer CounterExample API if present
            if hasattr(cex_obj, "to_dict"):
                result["cex"] = cex_obj.to_dict()
            else:
                result["cex"] = dict(cex_obj)
        except Exception:
            result["cex"] = str(cex_obj)
    if warning:
        result["warning"] = warning

    (cex_dir / f"validator_result_{cex_index}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def _to_state_dict(cex) -> Dict[str, object]:
    try:
        # CounterExample API
        return dict(cex.failing_state)
    except Exception:
        return dict(cex)


def validate_cex_list_extracted(
    extracted_file: Path,
    counter_examples: List[CounterExample],
    validation_dir: Path,
) -> List[Dict[str, object]]:
    """Validate a list of CEXs on the extracted harness, one subdir per CEX.

    Under validation_dir (e.g., try_dir/harness_before), we create subdirectories
    cex_0/, cex_1/, ... Each contains the injected program and per-cex result.
    A batch summary batch_results.json is also written under validation_dir.
    """
    results: List[Dict[str, object]] = []
    for cex in counter_examples:
        cex_dir = validation_dir / f"cex_{cex.cex_index}"
        state = _to_state_dict(cex)
        res = validate_extracted_cex(
            extracted_file=extracted_file,
            cex_assignments=state,
            cex_dir=cex_dir,
            cex_index=cex.cex_index,
            cex_obj=cex,
        )
        res["cex_index"] = cex.cex_index
        results.append(res)
    (validation_dir / "batch_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    return results


def validate_blocking_on_extracted(
    repaired_extracted_file: Path,
    cex_assignments: Dict[str, object],
    cex_dir: Path,
    cex_index: str,
    cex_obj: CounterExample,
    orig_failure_region: str,
) -> Dict[str, object]:
    """Validate that a CEX is blocked by the strengthened invariants.

    Returns the validator result augmented with:
      - blocked: comparative decision using orig_failure_region if provided;
                 otherwise fallback to (detected and failure_region == "before").
    """
    res = validate_extracted_cex(
        extracted_file=repaired_extracted_file,
        cex_assignments=cex_assignments,
        cex_dir=cex_dir,
        cex_index=cex_index,
        cex_obj=cex_obj,
    )
    # Compilation errors are not considered validated or blocked
    if bool(res.get("compilation_error")):
        res["blocked"] = False
        res["orig_failure_region"] = orig_failure_region
        (cex_dir / f"validator_blocking_result_{res.get('cex_index')}.json").write_text(
            json.dumps(res, indent=2), encoding="utf-8"
        )
        return res

    mut_detected = bool(res.get("detected"))
    mut_failureregion = res.get("failure_region")
    if orig_failure_region:
        res["blocked"] = _is_blocked(
            orig_failure_region, mut_detected, mut_failureregion
        )
        res["orig_failure_region"] = orig_failure_region
    else:
        res["blocked"] = bool(mut_detected and mut_failureregion == "before")
        res["orig_failure_region"] = None
        raise ValueError(
            f"orig_failure_region is missing for {cex_dir} {cex_index} {repaired_extracted_file}"
        )
    # Save per-cex result alongside the injected program directory
    (cex_dir / f"validator_blocking_result_{res.get('cex_index')}.json").write_text(
        json.dumps(res, indent=2), encoding="utf-8"
    )
    return res


def validate_blocking_list_extracted(
    repaired_extracted_file: Path,
    counter_examples: List[CounterExample],
    validation_dir: Path,
    baseline_regions: Optional[Dict[int, Optional[str]]] = None,
    baseline_results_path: Optional[Path] = None,
) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    if (
        baseline_regions is None
        and baseline_results_path
        and Path(baseline_results_path).exists()
    ):
        baseline_regions = _load_baseline_regions(Path(baseline_results_path))

    for cex in counter_examples:
        cex_dir = validation_dir / f"blocked_cex_{cex.cex_index}"
        state = _to_state_dict(cex)
        res = validate_blocking_on_extracted(
            repaired_extracted_file,
            state,
            cex_dir,
            cex_index=cex.cex_index,
            cex_obj=cex,
            orig_failure_region=baseline_regions.get(cex.cex_index),
        )
        res["cex_index"] = cex.cex_index
        results.append(res)
    (validation_dir / "batch_blocking_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    # log how many counter examples are blocked
    blocked_count = sum(1 for r in results if bool(r.get("blocked")))
    logger.info(
        f"Blocked {blocked_count} out of {len(results)} counter examples for {repaired_extracted_file}"
    )

    return results


__all__ = [
    "validate_extracted_cex",
    "validate_cex_list_extracted",
    "validate_blocking_on_extracted",
    "validate_blocking_list_extracted",
]
