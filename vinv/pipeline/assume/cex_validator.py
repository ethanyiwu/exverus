#!/usr/bin/env python3
"""
Counterexample validator for assume/assert-converted Verus programs.

Given a converted program (string or file) and a variable assignment map,
inject the assignment into the harness tuple-let and run Verus to see whether
an assertion failure is detected.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional

from vinv.pipeline.assume.cex_utils import inject_assignment_into_converted_syn
from vinv.verus_utils import verify_with_verus


def validate_cex_on_converted_code(
    converted_code: str,
    assignments: Dict[str, object],
    work_dir: Optional[Path] = None,
    use_old_verus: bool = False,
) -> Dict[str, object]:
    """
    Validate whether a candidate counterexample is detected by the converted program.

    - Injects the assignment into the first harness function (…_whileN) tuple-let.
    - Runs Verus on the injected file.

    Returns dict with keys:
      - detected (bool): True if Verus reports a verification error (assert fails)
      - injected_path (str): path to the injected file
      - produced_let_line (str): concrete let line used for injection (or "")
      - verus_stdout (str)
      - verus_stderr (str)
    """
    # Prepare working directory
    if work_dir is None:
        tmp_ctx = tempfile.TemporaryDirectory()
        work_dir_path = Path(tmp_ctx.name)
        owns_dir = True
    else:
        work_dir_path = Path(work_dir).resolve()
        work_dir_path.mkdir(parents=True, exist_ok=True)
        tmp_ctx = None
        owns_dir = False

    try:
        injected_code, let_line = inject_assignment_into_converted_syn(
            converted_code, assignments
        )
        injected_path = work_dir_path / "injected.rs"
        injected_path.write_text(injected_code, encoding="utf-8")

        # Run Verus
        out_file = work_dir_path / "injected_verus_out.txt"
        err_file = work_dir_path / "injected_verus_err.txt"
        ok = verify_with_verus(
            proof_file=injected_path,
            stdout_file=out_file,
            stderr_file=err_file,
            use_old_verus=use_old_verus,
        )
        verus_stdout = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
        verus_stderr = err_file.read_text(encoding="utf-8") if err_file.exists() else ""

        # In this context, a failure (ok == False) indicates an assertion violation was detected
        detected = not ok
        return {
            "detected": detected,
            "injected_path": str(injected_path),
            "produced_let_line": let_line,
            "verus_stdout": verus_stdout,
            "verus_stderr": verus_stderr,
        }
    finally:
        if owns_dir and tmp_ctx is not None:
            tmp_ctx.cleanup()


def validate_cex_on_file(
    converted_file: Path,
    assignments: Dict[str, object],
    work_dir: Optional[Path] = None,
    use_old_verus: bool = False,
) -> Dict[str, object]:
    converted_code = Path(converted_file).read_text(encoding="utf-8")
    return validate_cex_on_converted_code(
        converted_code, assignments, work_dir=work_dir, use_old_verus=use_old_verus
    )


def _load_assignments(
    assign_json: Optional[str], kv_list: Optional[list[str]]
) -> Dict[str, object]:
    result: Dict[str, object] = {}
    if assign_json:
        with open(assign_json, "r", encoding="utf-8") as f:
            payload = json.load(f)
        # Allow {"assignments": {...}} or a flat mapping
        if (
            isinstance(payload, dict)
            and "assignments" in payload
            and isinstance(payload["assignments"], dict)
        ):
            payload = payload["assignments"]
        if not isinstance(payload, dict):
            raise ValueError("JSON must be an object mapping variable -> value")
        result.update(payload)
    if kv_list:
        for kv in kv_list:
            if "=" not in kv:
                raise ValueError(f"Invalid assignment '{kv}', expected key=value")
            k, v = kv.split("=", 1)
            k = k.strip()
            v = v.strip()
            # Keep as string; inject_cex accepts Rust-like syntax strings
            result[k] = v
    return result


def main():
    parser = argparse.ArgumentParser(
        prog="cex_validator",
        description="Validate if a counterexample is detected by an assume/assert-converted Verus program.",
    )
    parser.add_argument(
        "converted", help="Path to the converted .rs file (contains harness _whileN)"
    )
    parser.add_argument(
        "--assign-json",
        help="Path to JSON file of assignments (var -> value or {'assignments': {...}})",
    )
    parser.add_argument(
        "--assign", action="append", help="Inline assignment key=value (repeatable)"
    )
    parser.add_argument(
        "--old-verus",
        action="store_true",
        help="Use OLD_VERUS_PATH instead of VERUS_PATH",
    )
    parser.add_argument(
        "--work-dir", help="Work directory for artifacts (default: temp dir)"
    )

    args = parser.parse_args()

    assignments = _load_assignments(args.assign_json, args.assign)
    if not assignments:
        raise SystemExit("No assignments provided; use --assign-json or --assign k=v")

    res = validate_cex_on_file(
        Path(args.converted),
        assignments,
        work_dir=Path(args.work_dir) if args.work_dir else None,
        use_old_verus=args.old_verus,
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
