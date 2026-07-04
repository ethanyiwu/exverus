from __future__ import annotations

import sys
from pathlib import Path

_AUTOVERUS_CODE_DIR = Path(__file__).resolve().parent.parent / "verus-proof-synthesis" / "code"
if _AUTOVERUS_CODE_DIR.is_dir() and str(_AUTOVERUS_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_AUTOVERUS_CODE_DIR))
