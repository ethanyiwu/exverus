from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from vinv.pipeline.parser_utils import extract_loop_for_error

BEFORE_LOOP_BODY_START = "// before loop body START"
BEFORE_LOOP_BODY_END = "// before loop body END"
AFTER_LOOP_BODY_START = "// after loop body START"
AFTER_LOOP_BODY_END = "// after loop body END"

_FN_RE = re.compile(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_LET_RE = re.compile(
    r"^\s*let\s+(?:mut\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^=;]+))?\s*="
)


@dataclass(frozen=True)
class HarnessTarget:
    name: str
    type_src: str | None
    source: str


@dataclass(frozen=True)
class ExtractedHarnessV2:
    path: Path
    source: str
    function_name: str
    injection_targets: list[HarnessTarget]
    insert_offset: int
    before_start_line: int | None
    before_end_line: int | None
    after_start_line: int | None
    after_end_line: int | None

    @property
    def injection_target_names(self) -> set[str]:
        return {target.name for target in self.injection_targets}


def prepare_extracted_harness_v2(
    proof_file: Path,
    verus_error: object,
    out_path: Path,
) -> ExtractedHarnessV2:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.exists():
        ok = extract_loop_for_error(proof_file, verus_error, out_path)
        if not ok:
            raise ValueError(f"Failed to extract loop harness for {proof_file}")
    return load_extracted_harness_v2(out_path)


def load_extracted_harness_v2(path: Path) -> ExtractedHarnessV2:
    source = path.read_text(encoding="utf-8")
    before_idx = source.find(BEFORE_LOOP_BODY_START)
    if before_idx < 0:
        raise ValueError(f"Missing {BEFORE_LOOP_BODY_START} in {path}")
    before_end_idx = source.find(BEFORE_LOOP_BODY_END)
    if before_end_idx < 0:
        raise ValueError(f"Missing {BEFORE_LOOP_BODY_END} in {path}")
    insert_offset = source.find("\n", before_idx)
    insert_offset = len(source) if insert_offset < 0 else insert_offset + 1
    function_name, targets = _parse_targets_before_marker(source, before_idx)
    return ExtractedHarnessV2(
        path=path,
        source=source,
        function_name=function_name,
        injection_targets=targets,
        insert_offset=insert_offset,
        before_start_line=_line_of_offset(source, before_idx),
        before_end_line=_line_of_offset(source, before_end_idx),
        after_start_line=_line_of_offset(source, source.find(AFTER_LOOP_BODY_START)),
        after_end_line=_line_of_offset(source, source.find(AFTER_LOOP_BODY_END)),
    )


def _parse_targets_before_marker(
    source: str, before_idx: int
) -> tuple[str, list[HarnessTarget]]:
    prefix = source[:before_idx]
    fn_matches = list(_FN_RE.finditer(prefix))
    if not fn_matches:
        raise ValueError("No function found before before-loop marker")
    fn_match = fn_matches[-1]
    function_name = fn_match.group(1)
    params_start = prefix.find("(", fn_match.start())
    params_end = _find_matching(prefix, params_start, "(", ")")
    body_start = prefix.find("{", params_end)
    if params_start < 0 or params_end < 0 or body_start < 0:
        raise ValueError(f"Could not parse harness signature for {function_name}")
    params_text = prefix[params_start + 1 : params_end]
    targets = [
        HarnessTarget(name=name, type_src=type_src, source="param")
        for name, type_src in _parse_params(params_text)
    ]
    body_prefix = prefix[body_start + 1 :]
    for line in body_prefix.splitlines():
        match = _LET_RE.match(line)
        if not match:
            continue
        targets.append(
            HarnessTarget(
                name=match.group(1),
                type_src=match.group(2).strip() if match.group(2) else None,
                source="local",
            )
        )
    return function_name, _dedupe_targets(targets)


def _parse_params(params_text: str) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = []
    for chunk in _split_top_level(params_text):
        text = chunk.strip()
        if not text or text == "&self" or text == "self":
            continue
        if ":" not in text:
            continue
        name, type_src = text.split(":", 1)
        name = name.strip().removeprefix("mut ").strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            params.append((name, type_src.strip()))
    return params


def _split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth_angle = 0
    depth_paren = 0
    depth_bracket = 0
    for ch in text:
        if ch == "<":
            depth_angle += 1
        elif ch == ">" and depth_angle > 0:
            depth_angle -= 1
        elif ch == "(":
            depth_paren += 1
        elif ch == ")" and depth_paren > 0:
            depth_paren -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]" and depth_bracket > 0:
            depth_bracket -= 1
        if (
            ch == ","
            and depth_angle == 0
            and depth_paren == 0
            and depth_bracket == 0
        ):
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _find_matching(text: str, start: int, open_ch: str, close_ch: str) -> int:
    if start < 0 or start >= len(text) or text[start] != open_ch:
        return -1
    depth = 0
    for idx in range(start, len(text)):
        char = text[idx]
        if char == open_ch:
            depth += 1
        elif char == close_ch:
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _dedupe_targets(targets: list[HarnessTarget]) -> list[HarnessTarget]:
    seen: set[str] = set()
    out: list[HarnessTarget] = []
    for target in targets:
        if target.name in seen:
            continue
        seen.add(target.name)
        out.append(target)
    return out


def _line_of_offset(source: str, offset: int) -> int | None:
    if offset < 0:
        return None
    return source[:offset].count("\n") + 1


__all__ = [
    "AFTER_LOOP_BODY_END",
    "AFTER_LOOP_BODY_START",
    "BEFORE_LOOP_BODY_END",
    "BEFORE_LOOP_BODY_START",
    "ExtractedHarnessV2",
    "HarnessTarget",
    "load_extracted_harness_v2",
    "prepare_extracted_harness_v2",
]
