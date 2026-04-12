#!/usr/bin/env python3
"""
Utilities for counterexample injection using verus_syn-based AST rewriting.

This avoids regex and delegates tuple-let assignment injection to a Rust tool
(`inject_cex`) that uses verus_syn to parse and edit the converted Verus program.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Tuple

from vinv.pipeline.parser_utils import find_or_build_rs_convert_bin


def _find_or_build_inject_bin() -> Path:
    return find_or_build_rs_convert_bin("inject_cex")


def inject_assignment_into_converted_syn(
    converted_code: str, assignments: Dict[str, object]
) -> Tuple[str, str]:
    """
    Replace the RHS tuple in the harness tuple-let assignment using verus_syn.

    Args:
        converted_code: full source of the converted Verus Rust module
        assignments: mapping var -> concrete value (as Python values or strings)

    Returns:
        (new_code, produced_let_line)
        - new_code: code after injection
        - produced_let_line: the concrete let line string used (empty if none)
    """
    bin_path = _find_or_build_inject_bin()

    # Normalize assignment values to strings Verus can parse
    def to_verus_expr(v: object) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return v
        if isinstance(v, (list, tuple)):
            inner = ", ".join(to_verus_expr(x) for x in v)
            return f"({inner})"
        return str(v)

    map_payload = {
        "assignments": {k: to_verus_expr(v) for (k, v) in assignments.items()},
    }

    with tempfile.TemporaryDirectory() as tmpd:
        tmp_dir = Path(tmpd)
        in_path = tmp_dir / "in.rs"
        out_path = tmp_dir / "out.rs"
        map_json = tmp_dir / "map.json"
        report_json = tmp_dir / "report.json"

        in_path.write_text(converted_code, encoding="utf-8")
        map_json.write_text(json.dumps(map_payload), encoding="utf-8")

        cmd = [
            str(bin_path),
            str(in_path),
            str(out_path),
            "--map-json",
            str(map_json),
            "--report-json",
            str(report_json),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"inject_cex failed: {e.stderr or e.stdout}")

        new_code = out_path.read_text(encoding="utf-8")

        produced_let_line = ""
        if report_json.exists():
            try:
                report = json.loads(report_json.read_text(encoding="utf-8"))
                lhs = report.get("lhs", [])
                if lhs:
                    rhs = [map_payload["assignments"].get(name, name) for name in lhs]
                    produced_let_line = (
                        f"let (mut {', mut '.join(lhs)}) = ({', '.join(rhs)});"
                    )
            except Exception:
                produced_let_line = ""

        return new_code, produced_let_line
