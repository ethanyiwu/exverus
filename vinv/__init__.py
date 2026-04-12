import sys
from pathlib import Path


def _bootstrap_autoverus_code_dir() -> None:
    code_dir = Path(__file__).resolve().parent.parent / "verus-proof-synthesis" / "code"
    code_dir_str = str(code_dir)
    if code_dir.is_dir() and code_dir_str not in sys.path:
        sys.path.insert(0, code_dir_str)


_bootstrap_autoverus_code_dir()
