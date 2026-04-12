#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger
from veval import VerusError, VerusErrorType

from vinv.config import ROOT_DIR


def find_or_build_rs_convert_bin(binary_name: str) -> Path:
    """Find or build a Rust tool binary under tool/rs/convert.

    Prefers release, falls back to debug; builds (debug) if neither exists.
    """
    tool_dir = ROOT_DIR / "tool" / "rs" / "convert"
    candidates = [
        tool_dir / "target" / "debug" / binary_name,
        tool_dir / "target" / "release" / binary_name,
    ]
    for c in candidates:
        if c.exists():
            return c
    subprocess.run(["cargo", "build", "--quiet"], cwd=str(tool_dir), check=True)
    debug_bin = tool_dir / "target" / "debug" / binary_name
    if not debug_bin.exists():
        raise RuntimeError(f"{binary_name} not built at {debug_bin}")
    return debug_bin


def get_target_line_from_error(verus_error: VerusError) -> Optional[int]:
    """Infer the target source line from a VerusError's trace/spans."""
    target_trace = verus_error.trace[-1]
    assert (
        "/tmp" in target_trace.fname
    ), f"Target trace fname is not in /tmp, full trace {target_trace.fname} {target_trace.get_lines()}"
    return target_trace.get_lines()[0]


def extract_loop_for_error(
    proof_file: Path, verus_error: VerusError, out_path: Path
) -> bool:
    """Run extract_loop_syn on proof_file for the error's target line into out_path.

    Mode selection:
      - InvFailFront -> check_base_case (assert invariants once, no body/condition)
      - otherwise    -> check_inductiveness (assert cond + invariants before/after body)
    """
    target_line = get_target_line_from_error(verus_error)
    if target_line is None:
        return False
    bin_path = find_or_build_rs_convert_bin("extract_loop_syn")
    mode = (
        "check_base_case"
        if verus_error.error == VerusErrorType.InvFailFront
        else "check_inductiveness"
    )

    cmd = [
        str(bin_path),
        str(proof_file),
        str(out_path),
        "--line",
        str(target_line),
        "--mode",
        mode,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out_path.exists()


def extract_loop_for_id(
    proof_file: Path,
    fn_name: str,
    loop_index: int,
    out_path: Path,
    verus_error: VerusError,
) -> bool:
    """Run extract_loop_syn on proof_file for a specific function and loop index.

    Uses the Rust extractor with explicit function name and 1-based loop index
    (order of while/for loops within that function), which is more stable than
    source line-based selection.
    """
    try:
        bin_path = find_or_build_rs_convert_bin("extract_loop_syn")
        mode = (
            "check_base_case"
            if verus_error.error == VerusErrorType.InvFailFront
            else "check_inductiveness"
        )
        cmd = [
            str(bin_path),
            str(proof_file),
            str(out_path),
            "--fn",
            str(fn_name),
            "--loop-index",
            str(int(loop_index)),
            "--mode",
            mode,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return out_path.exists()
    except Exception as e:
        logger.warning(f"Failed to extract loop harness by id: {e}")
        return False


def read_loop_id_from_extracted(extracted_file: Path) -> Optional[Tuple[str, int]]:
    """Recover (original_fn_name, loop_index) from an extracted harness.

    Tries the Rust verus_syn-based reader first (robust to formatting),
    then falls back to a regex-based parse if the tool isn't available.
    """
    # Try Rust helper first
    bin_path = find_or_build_rs_convert_bin("read_loop_id_syn")
    cp = subprocess.run(
        [str(bin_path), str(extracted_file)],
        check=True,
        capture_output=True,
        text=True,
    )
    out = cp.stdout.strip()
    parts = out.split()
    if len(parts) == 2:
        orig, idx_s = parts
        return (orig, int(idx_s))

    raise ValueError(f"Failed to read loop id from {extracted_file}")


def _find_verus_block(src: str) -> Optional[Tuple[int, int]]:
    """Find the byte-range (start, end) for the first `verus! { ... }` block in src.

    Returns (start_open_brace, matching_close_brace_index) where indices are into src.
    """
    target = "verus!"
    i = 0
    n = len(src)
    while i + len(target) <= n:
        if src[i : i + len(target)] == target:
            j = i + len(target)
            while j < n and src[j].isspace():
                j += 1
            if j < n and src[j] == "{":
                start = j
                depth = 0
                k = j
                while k < n:
                    c = src[k]
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        if depth == 0:
                            break
                        depth -= 1
                        if depth == 0:
                            return (start, k)
                    k += 1
        i += 1
    return None


def error_inside_loop(proof_file: Path, verus_error: VerusError) -> bool:
    """Return True if the target error location is within a loop body.

    Uses the existing Rust extractor: if it can extract a loop harness at the
    error's target line, we conclude the error is inside a loop.
    """
    try:
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "extracted_loop.rs"
            return extract_loop_for_error(proof_file, verus_error, out_path)
    except Exception:
        logger.info(f"error {verus_error.error} is not inside a loop")
        return False


__all__ = [
    "find_or_build_rs_convert_bin",
    "get_target_line_from_error",
    "extract_loop_for_error",
    "extract_loop_for_id",
    "read_loop_id_from_extracted",
    "error_inside_loop",
]
