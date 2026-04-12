#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict

from vinv.pipeline.parser_utils import find_or_build_rs_convert_bin


def _find_or_build_bin() -> Path:
    return find_or_build_rs_convert_bin("inject_cex_extracted")


def inject_into_extracted_code(
    cex_dir: Path,
    extracted_file: Path,
    injected_file: Path,
    assignments: Dict[str, object],
):
    # Pass through raw JSON values; conversion to typed Rust/Verus expressions is handled in the injector.
    payload = {"assignments": assignments}

    tool = _find_or_build_bin()
    map_path = cex_dir / "map.json"
    map_path.write_text(json.dumps(payload), encoding="utf-8")

    cmd = [
        str(tool),
        str(extracted_file),
        str(injected_file),
        "--map-json",
        str(map_path),
    ]
    subprocess.run(cmd, check=True)


__all__ = ["inject_into_extracted_code"]
