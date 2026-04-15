from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from loguru import logger
from veval import VerusErrorType, VEval

from vinv.pipeline.cex_harness_v2 import (
    AFTER_LOOP_BODY_END,
    AFTER_LOOP_BODY_START,
    BEFORE_LOOP_BODY_END,
    BEFORE_LOOP_BODY_START,
    ExtractedHarnessV2,
    load_extracted_harness_v2,
)
from vinv.pipeline.counter_example import CounterExample
from vinv.verus_utils import verus_format

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INT_RE = re.compile(r"^[+-]?\d+(?:u\d+|i\d+|usize|isize)?$")
_PRE_SUFFIXES = ("_pre", "_before")
_POST_SUFFIXES = ("_post", "_after")


@dataclass(frozen=True)
class NormalizedCounterexampleV2:
    raw_assignments: dict[str, object]
    injected_assignments: dict[str, object]
    post_state_hints: dict[str, object]
    alias_map: dict[str, str]
    dropped_keys: list[str]


def normalize_counterexample_v2(
    raw_assignments: Mapping[str, object],
    harness: ExtractedHarnessV2,
) -> NormalizedCounterexampleV2:
    injected: dict[str, object] = {}
    post_hints: dict[str, object] = {}
    alias_map: dict[str, str] = {}
    dropped: list[str] = []
    vec_entries: dict[str, dict[int, object]] = {}
    vec_lengths: dict[str, int] = {}
    post_vec_entries: dict[str, dict[int, object]] = {}
    post_vec_lengths: dict[str, int] = {}
    names = harness.injection_target_names

    for key, value in raw_assignments.items():
        if not isinstance(key, str):
            dropped.append(str(key))
            continue
        vec_info = _parse_vec_key(key)
        if vec_info is not None:
            base, idx, is_len, state = vec_info
            if base not in names:
                dropped.append(key)
                continue
            target_entries = post_vec_entries if state == "post" else vec_entries
            target_lengths = post_vec_lengths if state == "post" else vec_lengths
            if is_len:
                try:
                    target_lengths[base] = int(value)
                    alias_map[key] = (
                        f"{base}_after" if state == "post" else base
                    )
                except Exception:
                    dropped.append(key)
                continue
            target_entries.setdefault(base, {})[idx] = value
            alias_map[key] = f"{base}_after" if state == "post" else base
            continue
        if key in names:
            injected[key] = value
            continue
        pre_base = _strip_suffix(key, _PRE_SUFFIXES)
        if pre_base in names and pre_base not in injected:
            injected[pre_base] = value
            alias_map[key] = pre_base
            continue
        post_base = _strip_suffix(key, _POST_SUFFIXES)
        if post_base in names:
            canonical = f"{post_base}_after"
            post_hints[canonical] = value
            alias_map[key] = canonical
            continue
        dropped.append(key)

    for base, entries in vec_entries.items():
        if base in injected:
            continue
        injected[base] = _coalesce_vec(entries, vec_lengths.get(base))
    for base, entries in post_vec_entries.items():
        canonical = f"{base}_after"
        if canonical in post_hints:
            continue
        post_hints[canonical] = _coalesce_vec(entries, post_vec_lengths.get(base))

    return NormalizedCounterexampleV2(
        raw_assignments={str(k): v for k, v in raw_assignments.items() if isinstance(k, str)},
        injected_assignments=injected,
        post_state_hints=post_hints,
        alias_map=alias_map,
        dropped_keys=sorted(dropped),
    )


def inject_counterexample_v2(
    harness: ExtractedHarnessV2,
    normalized: NormalizedCounterexampleV2,
    injected_file: Path,
) -> None:
    indent = _indent_of_line(harness.source, harness.insert_offset)
    lines: list[str] = []
    if "i" not in harness.injection_target_names:
        lines.append(f"{indent}let mut i: usize = 0usize;")
    for target in harness.injection_targets:
        if target.name not in normalized.injected_assignments:
            continue
        expr = _render_value(normalized.injected_assignments[target.name], target.type_src)
        lines.append(f"{indent}let mut {target.name} = {expr};")
    text = "\n".join(lines)
    if text:
        text += "\n"
    injected = (
        harness.source[: harness.insert_offset] + text + harness.source[harness.insert_offset :]
    )
    injected_file.write_text(injected, encoding="utf-8")


def validate_extracted_cex_v2(
    extracted_file: Path,
    cex_assignments: Dict[str, object],
    cex_dir: Path,
    cex_index: int | str,
    cex_obj: CounterExample | Mapping[str, object] | None,
) -> Dict[str, object]:
    cex_dir.mkdir(parents=True, exist_ok=True)
    harness = load_extracted_harness_v2(extracted_file)
    normalized = normalize_counterexample_v2(cex_assignments, harness)
    injected_file = cex_dir / "injected_cex.rs"
    inject_counterexample_v2(harness, normalized, injected_file)
    try:
        verus_format(injected_file)
    except Exception:
        logger.debug(f"Failed to format injected harness {injected_file}")

    evaluator = VEval(injected_file.read_text(encoding="utf-8"), logger)
    evaluator.eval_and_get_score(max_errs=10, json_mode=True)

    verification_passed = evaluator.get_errors() == 0 and not evaluator.compilation_error
    error_names: list[str] = []
    assert_fail_lines: list[int] = []
    detected = False
    for failure in evaluator.get_failures():
        error_names.append(failure.error.name)
        if failure.error != VerusErrorType.AssertFail:
            continue
        detected = True
        for trace in failure.trace:
            line_no, _ = trace.get_lines()
            if isinstance(line_no, int) and line_no > 0:
                assert_fail_lines.append(line_no)

    if evaluator.compilation_error:
        detected = False
        failure_region = None
        if "CompilationError" not in error_names:
            error_names.append("CompilationError")
    else:
        failure_region = _classify_failure_region(
            injected_file.read_text(encoding="utf-8"), assert_fail_lines
        )

    result: dict[str, object] = {
        "verification_passed": verification_passed,
        "detected": bool(detected and not verification_passed),
        "failure_region": failure_region,
        "injected_file": str(injected_file),
        "errors": error_names,
        "cex_index": cex_index,
        "compilation_error": bool(evaluator.compilation_error),
        "normalized_assignments": normalized.injected_assignments,
        "post_state_hints": normalized.post_state_hints,
        "alias_map": normalized.alias_map,
        "dropped_keys": normalized.dropped_keys,
        "injected_names": [
            target.name
            for target in harness.injection_targets
            if target.name in normalized.injected_assignments
        ],
    }
    if cex_obj is not None:
        result["cex"] = _serialize_cex(cex_obj)
    (cex_dir / f"validator_result_{cex_index}.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )
    return result


def validate_cex_list_extracted_v2(
    extracted_file: Path,
    counter_examples: List[CounterExample],
    validation_dir: Path,
) -> List[Dict[str, object]]:
    results: list[dict[str, object]] = []
    for cex in counter_examples:
        cex_dir = validation_dir / f"cex_{cex.cex_index}"
        result = validate_extracted_cex_v2(
            extracted_file=extracted_file,
            cex_assignments=dict(cex.failing_state),
            cex_dir=cex_dir,
            cex_index=cex.cex_index,
            cex_obj=cex,
        )
        results.append(result)
    (validation_dir / "batch_results.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    return results


def validate_blocking_on_extracted_v2(
    repaired_extracted_file: Path,
    cex_assignments: Dict[str, object],
    cex_dir: Path,
    cex_index: int | str,
    cex_obj: CounterExample | Mapping[str, object] | None,
    orig_failure_region: Optional[str],
) -> Dict[str, object]:
    result = validate_extracted_cex_v2(
        extracted_file=repaired_extracted_file,
        cex_assignments=cex_assignments,
        cex_dir=cex_dir,
        cex_index=cex_index,
        cex_obj=cex_obj,
    )
    blocked, reason = _blocking_decision(
        orig_failure_region=orig_failure_region,
        compilation_error=bool(result.get("compilation_error")),
        detected=bool(result.get("detected")),
        failure_region=result.get("failure_region"),
    )
    result["blocked"] = blocked
    result["blocking_reason"] = reason
    result["orig_failure_region"] = orig_failure_region
    (cex_dir / f"validator_blocking_result_{cex_index}.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )
    return result


def validate_blocking_list_extracted_v2(
    repaired_extracted_file: Path,
    counter_examples: List[CounterExample],
    validation_dir: Path,
    baseline_regions: Optional[Dict[int, Optional[str]]] = None,
    baseline_results_path: Optional[Path] = None,
) -> List[Dict[str, object]]:
    regions = baseline_regions or _load_baseline_regions_v2(baseline_results_path)
    results: list[dict[str, object]] = []
    for cex in counter_examples:
        cex_dir = validation_dir / f"blocked_cex_{cex.cex_index}"
        result = validate_blocking_on_extracted_v2(
            repaired_extracted_file=repaired_extracted_file,
            cex_assignments=dict(cex.failing_state),
            cex_dir=cex_dir,
            cex_index=cex.cex_index,
            cex_obj=cex,
            orig_failure_region=regions.get(int(cex.cex_index)),
        )
        results.append(result)
    (validation_dir / "batch_blocking_results.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    return results


def _serialize_cex(cex_obj: CounterExample | Mapping[str, object]) -> object:
    if isinstance(cex_obj, CounterExample):
        return cex_obj.to_dict()
    return dict(cex_obj)


def _parse_vec_key(key: str) -> tuple[str, int, bool, str] | None:
    parsed = _parse_namespaced_vec_key(key)
    if parsed is not None:
        return parsed
    parsed = _parse_legacy_vec_key(key)
    if parsed is not None:
        return parsed
    return None


def _parse_namespaced_vec_key(key: str) -> tuple[str, int, bool, str] | None:
    if not key.startswith("__vec__"):
        return None
    body = key[len("__vec__") :]
    if "__" not in body:
        return None
    base, tail = body.split("__", 1)
    state = ""
    for suffix in _POST_SUFFIXES + _PRE_SUFFIXES:
        if tail.endswith(suffix):
            state = suffix.removeprefix("_")
            tail = tail[: -len(suffix)]
            break
    return _normalize_vec_parts(base, tail, state)


def _parse_legacy_vec_key(key: str) -> tuple[str, int, bool, str] | None:
    state = ""
    base_tail = key
    for suffix in _POST_SUFFIXES + _PRE_SUFFIXES:
        if key.endswith(suffix):
            state = suffix.removeprefix("_")
            base_tail = key[: -len(suffix)]
            break
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)_(\d+|len)$", base_tail)
    if match is not None:
        return _normalize_vec_parts(match.group(1), match.group(2), state)
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*?)_(pre|before|post|after)_(\d+|len)$", key)
    if match is not None:
        return _normalize_vec_parts(match.group(1), match.group(3), match.group(2))
    return None


def _normalize_vec_parts(
    base: str,
    tail: str,
    state: str,
) -> tuple[str, int, bool, str] | None:
    kind = _state_kind(state)
    state_base = _strip_suffix(base, _POST_SUFFIXES)
    if state_base:
        base = state_base
        kind = "post"
    else:
        pre_base = _strip_suffix(base, _PRE_SUFFIXES)
        if pre_base:
            base = pre_base
            kind = "plain"
    if not _IDENT_RE.fullmatch(base):
        return None
    if tail == "len":
        return base, -1, True, kind
    if not tail.isdigit():
        return None
    return base, int(tail), False, kind


def _strip_suffix(name: str, suffixes: Iterable[str]) -> str:
    for suffix in suffixes:
        if name.endswith(suffix) and len(name) > len(suffix):
            candidate = name[: -len(suffix)]
            if _IDENT_RE.fullmatch(candidate):
                return candidate
    return ""


def _state_kind(state: str) -> str:
    if state in {"post", "after"}:
        return "post"
    return "plain"


def _coalesce_vec(entries: Mapping[int, object], length: Optional[int]) -> str:
    if length is None:
        indices = sorted(entries)
    else:
        indices = [idx for idx in range(length) if idx in entries]
        if not indices:
            indices = sorted(entries)
    return f"vec![{', '.join(_render_value(entries[idx], None) for idx in indices)}]"


def _render_value(value: object, type_src: str | None) -> str:
    ty = (type_src or "").replace(" ", "")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        if "usize" in ty:
            return f"{value}usize"
        if "u128" in ty:
            return f"{value}u128"
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        return f"vec![{', '.join(_render_value(item, _vec_inner_type(ty)) for item in value)}]"
    if not isinstance(value, str):
        return str(value)
    text = value.strip()
    if not text:
        return '""' if "String" in ty or "&str" in ty else text
    if "String" in ty or "&str" in ty:
        return json.dumps(value)
    if _is_vec_type(ty) and text.startswith("[") and text.endswith("]"):
        return f"vec!{text}"
    return text


def _vec_inner_type(type_src: str) -> str | None:
    if "Vec<" not in type_src:
        return None
    start = type_src.find("Vec<") + 4
    end = type_src.rfind(">")
    if end <= start:
        return None
    return type_src[start:end]


def _is_vec_type(type_src: str) -> bool:
    return "Vec<" in type_src


def _indent_of_line(source: str, offset: int) -> str:
    line_start = source.rfind("\n", 0, offset) + 1
    line_end = source.find("\n", line_start)
    if line_end < 0:
        line_end = len(source)
    line = source[line_start:line_end]
    return line[: len(line) - len(line.lstrip(" "))]


def _classify_failure_region(source: str, assert_fail_lines: list[int]) -> Optional[str]:
    if not assert_fail_lines:
        return None
    lines = source.splitlines()
    markers = {
        BEFORE_LOOP_BODY_START: None,
        BEFORE_LOOP_BODY_END: None,
        AFTER_LOOP_BODY_START: None,
        AFTER_LOOP_BODY_END: None,
    }
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped in markers:
            markers[stripped] = idx
    before_start = markers[BEFORE_LOOP_BODY_START]
    before_end = markers[BEFORE_LOOP_BODY_END]
    after_start = markers[AFTER_LOOP_BODY_START]
    after_end = markers[AFTER_LOOP_BODY_END]
    if before_start is None and after_start is None:
        return "before"
    if _any_in_range(assert_fail_lines, before_start, before_end):
        return "before"
    if _any_in_range(assert_fail_lines, after_start, after_end):
        return "after"
    if (
        after_start is not None
        and any(line_no < after_start for line_no in set(assert_fail_lines))
    ):
        return "before"
    return "neither"


def _any_in_range(
    line_numbers: Iterable[int],
    start: Optional[int],
    end: Optional[int],
) -> bool:
    if start is None or end is None:
        return False
    return any(start <= line_no <= end for line_no in set(line_numbers))


def _load_baseline_regions_v2(
    baseline_results_path: Optional[Path],
) -> Dict[int, Optional[str]]:
    if baseline_results_path is None or not baseline_results_path.is_file():
        return {}
    data = json.loads(baseline_results_path.read_text(encoding="utf-8"))
    regions: dict[int, Optional[str]] = {}
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("cex_index"), int):
            continue
        regions[int(item["cex_index"])] = item.get("failure_region")
    return regions


def _blocking_decision(
    orig_failure_region: Optional[str],
    compilation_error: bool,
    detected: bool,
    failure_region: object,
) -> tuple[bool, str]:
    if compilation_error:
        return False, "compilation_error"
    if orig_failure_region == "before":
        if not detected:
            return True, "target_disappeared"
        return False, "target_still_before" if failure_region == "before" else "target_shifted"
    if orig_failure_region == "after":
        if not detected:
            return True, "target_disappeared"
        if failure_region == "before":
            return True, "moved_before"
        return False, "target_still_after" if failure_region == "after" else "target_shifted"
    return False, "missing_baseline_region"


__all__ = [
    "NormalizedCounterexampleV2",
    "inject_counterexample_v2",
    "normalize_counterexample_v2",
    "validate_blocking_list_extracted_v2",
    "validate_cex_list_extracted_v2",
    "validate_extracted_cex_v2",
]
