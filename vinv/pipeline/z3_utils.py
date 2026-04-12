"""
Utilities for executing assistant-generated Python Z3 scripts with timeouts.

We execute the code in a subprocess to enforce a hard wall-clock timeout and
also set Z3's own per-check timeout via z3.set_param(timeout=ms) inside the child.
"""

from __future__ import annotations

import multiprocessing as _mp
from multiprocessing.queues import Queue as _MPQueue  # type: ignore
from typing import Any, Dict, List, Optional, Tuple


def _z3_run_worker(
    q: _MPQueue,
    code_str: str,
    per_call_timeout_ms: int,
    status_k: Optional[str],
    keys: List[str],
) -> None:
    """Top-level worker for multiprocessing to avoid pickling local functions on macOS spawn."""
    try:
        import z3  # type: ignore

        z3.set_param(timeout=per_call_timeout_ms)
        ns: Dict[str, Any] = {"z3": z3}
        if status_k:
            ns[status_k] = None
        for k in keys:
            ns[k] = None
        exec(code_str, ns)
        status_val = ns.get(status_k) if status_k else None
        result_map = {k: ns.get(k) for k in keys}
        q.put(("ok", status_val, result_map))
    except Exception as e:
        try:
            q.put(("err", None, f"{e}"))
        except Exception:
            pass


def run_z3_script_with_timeout(
    code: str,
    timeout_seconds: int,
    status_key: Optional[str],
    capture_keys: List[str],
) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
    """Run a Python Z3 script in a subprocess with timeouts.

    Args:
        code: Assistant-provided Python code to execute.
        timeout_seconds: Hard wall-clock timeout for the entire execution.
        status_key: Name of a global to read as status (e.g., "__z3_cex_status__"), or None.
        capture_keys: Global names to capture from the executed namespace.

    Returns:
        status (lowercased str or None), captured (dict of key -> value), error (str or None).
    """

    # Prefer 'fork' on POSIX to avoid macOS 'spawn' requiring an importable __main__ file
    try:
        start_m = _mp.get_start_method(allow_none=True)
        if start_m != "fork":
            _mp.set_start_method("fork", force=True)
    except Exception:
        # If not supported or already set, continue with defaults
        pass

    q: _MPQueue = _mp.Queue()
    per_check_timeout_ms = max(1, int(timeout_seconds * 1000))
    p = _mp.Process(
        target=_z3_run_worker,
        args=(q, code, per_check_timeout_ms, status_key, capture_keys),
    )
    p.start()
    p.join(timeout_seconds)
    if p.is_alive():
        try:
            p.terminate()
        finally:
            p.join(1)
        return None, {}, "Z3 script execution timed out"

    try:
        tag, a, b = q.get_nowait()
    except Exception:
        return None, {}, "Z3 script terminated without producing results"

    if tag == "ok":
        status_norm = str(a).strip().lower() if a is not None else None
        return status_norm, b, None
    return None, {}, str(b)
