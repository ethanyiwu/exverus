from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    obfuscator = Path(__file__).with_name("obfuscation_copilot.py")
    case_root = repo_root / "VeruSAGE_sampled"
    case_list = case_root / "sampled_task_ids.txt"

    cmd = [
        sys.executable,
        str(obfuscator),
        "--case-list",
        str(case_list),
        "--case-root",
        str(case_root),
    ]
    cmd.extend(sys.argv[1:])
    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
