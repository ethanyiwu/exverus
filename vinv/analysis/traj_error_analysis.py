"""
Filter pipeline trajectory try_* directories by:
1) `repaired_verify_status.txt` == status (default: verification_error)
2) the SET of error types extracted from `repaired_err.txt` matches a target set
   (default target: {"AssertFail"}).

Output:
- Always prints a short summary to stderr.
- With `--print`, prints JSON-lines records for each matching try_* dir.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set

from loguru import logger

from vinv.utils import json_load

DEFAULT_TECHNIQUE = "cex_repair_z3_mut_val_10"
DEFAULT_STATUS = "verification_error"
DEFAULT_ERRORS = "AssertFail"


def _repo_root() -> Path:
    # vinv/analysis/traj_error_analysis.py -> parents:
    # 0: analysis, 1: vinv, 2: repo root
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _repo_root()
ENTRY_JSON = REPO_ROOT / "vinv" / "analysis" / "entry.json"
PIPELINE_ROOT = REPO_ROOT / "results" / "pipeline"
VEVAL_PY = REPO_ROOT / "verus-proof-synthesis" / "code" / "veval.py"


def _load_veval_message_to_type_name() -> Dict[str, str]:
    """
    Load the message -> VerusErrorType.name mapping from `verus-proof-synthesis/code/veval.py`
    without importing it (importing veval has environment side effects like requiring `verus`).
    """
    if not VEVAL_PY.is_file():
        return {}
    mapping: Dict[str, str] = {}
    in_map = False
    for raw in VEVAL_PY.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not in_map:
            if line.startswith("m2VerusError") and "{" in line:
                in_map = True
            continue
        if line.startswith("}"):
            break
        # Example line:
        # "assertion failed": VerusErrorType.AssertFail,
        if not line.startswith('"'):
            continue
        try:
            msg = line.split('"', 2)[1]
        except Exception:
            continue
        # Parse type name after `VerusErrorType.`
        marker = "VerusErrorType."
        if marker not in line:
            continue
        tail = line.split(marker, 1)[1]
        # take identifier prefix
        tname = ""
        for ch in tail:
            if ch.isalnum() or ch == "_":
                tname += ch
            else:
                break
        if msg and tname:
            mapping[msg] = tname
    return mapping


_VEVAL_MSG2TYPE: Dict[str, str] | None = None


def _msg_to_type_name(msg: str) -> str:
    global _VEVAL_MSG2TYPE
    if _VEVAL_MSG2TYPE is None:
        _VEVAL_MSG2TYPE = _load_veval_message_to_type_name()
    return _VEVAL_MSG2TYPE.get(msg, msg)


def _as_str_list(obj: Dict, key: str) -> List[str]:
    val = obj.get(key)
    if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
        raise ValueError(f"Expected `{key}` to be a list[str] in entry.json")
    return [x.strip() for x in val if x and x.strip()]


def _is_try_dir(p: Path) -> bool:
    if not p.is_dir():
        return False
    if not p.name.startswith("try_"):
        return False
    suffix = p.name.split("_")[-1]
    try:
        int(suffix)
        return True
    except Exception:
        return False


def _parse_focus_errors(s: str) -> Set[str]:
    """
    Comma-separated tokens.

    Each token may be:
    - a canonical veval-style type name: AssertFail, PostCondFail, ...
    - or a raw veval message: "assertion failed", ...
    - or an arbitrary string (kept as-is)
    """
    s = (s or "").strip()
    if not s:
        return set()

    toks = [t.strip() for t in s.split(",") if t.strip()]
    out: Set[str] = set()
    # Allow raw veval messages ("postcondition not satisfied") as well as type names ("PostCondFail").
    for t in toks:
        out.add(_msg_to_type_name(t))
    return out


def _match_error_set(found: Set[str], focus: Set[str], mode: str) -> bool:
    """
    mode:
      - exact: found == focus
      - contains: found ⊇ focus
      - contained_by: found ⊆ focus
    """
    if not focus:
        return True
    if mode == "exact":
        return found == focus
    if mode == "contains":
        return found.issuperset(focus)
    if mode == "contained_by":
        return found.issubset(focus)
    raise ValueError(f"Unknown match_mode: {mode}")


def _error_set_from_repaired_err(err_file: Path) -> Set[str]:
    """
    Extract a SET of canonical error-type names from `repaired_err.txt`.

    `repaired_err.txt` is human-readable and contains lines like:
      error: postcondition not satisfied
    We map these messages via `veval.m2VerusError` to canonical `VerusErrorType.name`
    (e.g. PostCondFail).
    """
    if not err_file.is_file():
        return set()

    out: Set[str] = set()
    for raw in err_file.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("error:"):
            continue
        msg = line[len("error:") :].strip()
        if not msg or msg.startswith("aborting due to"):
            continue
        out.add(_msg_to_type_name(msg))
    return out


def _iter_try_dirs_for_model_benchmark(
    pipeline_root: Path, model: str, benchmark: str, technique: str
):
    bench_root = pipeline_root / model / benchmark
    if not bench_root.is_dir():
        return

    for technique_dir in bench_root.rglob(technique):
        if not technique_dir.is_dir() or technique_dir.name != technique:
            continue
        for try_dir in technique_dir.rglob("try_*"):
            if _is_try_dir(try_dir):
                yield try_dir


def scan(
    technique: str = DEFAULT_TECHNIQUE,
    status: str = DEFAULT_STATUS,
    errors: str = DEFAULT_ERRORS,
    match: str = "exact",
    print_matches: bool = False,
) -> Dict[str, int]:
    technique = (technique or "").strip()
    if not technique:
        raise ValueError("technique must be non-empty")

    status = (status or "").strip()
    if not status:
        raise ValueError("status must be non-empty")

    if not ENTRY_JSON.is_file():
        raise FileNotFoundError(f"entry.json not found: {ENTRY_JSON}")
    if not PIPELINE_ROOT.is_dir():
        raise FileNotFoundError(f"pipeline root not found: {PIPELINE_ROOT}")

    focus_set = _parse_focus_errors(errors)
    entry = json_load(ENTRY_JSON)
    models = _as_str_list(entry, "models")
    benchmarks = _as_str_list(entry, "benchmarks")

    scanned_try_dirs = 0
    status_matched = 0
    err_file_present = 0
    error_set_matched = 0

    def _emit_summary() -> None:
        logger.info(
            f"[traj_error_analysis] scanned_try_dirs={scanned_try_dirs} "
            f"status_matched={status_matched} err_file_present={err_file_present} "
            f"error_set_matched={error_set_matched} status={status} "
            f"errors={sorted(focus_set)} match={match}"
        )

    for model in models:
        for benchmark in benchmarks:
            for try_dir in _iter_try_dirs_for_model_benchmark(
                pipeline_root=PIPELINE_ROOT,
                model=model,
                benchmark=benchmark,
                technique=technique,
            ):
                scanned_try_dirs += 1

                status_file = try_dir / "repaired_verify_status.txt"
                if not status_file.is_file():
                    continue
                if status_file.read_text(errors="replace").strip() != status:
                    continue
                status_matched += 1

                err_file = try_dir / "repaired_err.txt"
                if not err_file.is_file():
                    continue
                err_file_present += 1

                found_from_log = _error_set_from_repaired_err(err_file)
                if not _match_error_set(found_from_log, focus_set, match):
                    continue

                # Offline mode: use log-derived errors only (fast).
                found_errors = found_from_log
                error_set_matched += 1

                print(f"try_dir: {try_dir}")
                if print_matches:
                    rec = {
                        "model": model,
                        "benchmark": benchmark,
                        "try_dir": try_dir.relative_to(PIPELINE_ROOT).as_posix(),
                        "errors": sorted(found_errors),
                    }
                    try:
                        print(json.dumps(rec))
                    except BrokenPipeError:
                        # Common when piping to `head`. Exit quietly.
                        sys.stdout.close()
                        _emit_summary()
                        return {
                            "scanned_try_dirs": scanned_try_dirs,
                            "status_matched": status_matched,
                            "err_file_present": err_file_present,
                            "error_set_matched": error_set_matched,
                        }

    _emit_summary()

    return {
        "scanned_try_dirs": scanned_try_dirs,
        "status_matched": status_matched,
        "err_file_present": err_file_present,
        "error_set_matched": error_set_matched,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Filter try_* dirs by repaired status + error-type set extracted from repaired_err.txt."
    )
    p.add_argument("--technique", default=DEFAULT_TECHNIQUE)
    p.add_argument("--status", default=DEFAULT_STATUS)
    p.add_argument(
        "--errors",
        default=DEFAULT_ERRORS,
        help='Comma-separated set, e.g. "AssertFail" or "assertion failed" or "AssertFail,PostCondFail".',
    )
    p.add_argument(
        "--match", choices=["exact", "contains", "contained_by"], default="exact"
    )
    p.add_argument(
        "--print", action="store_true", help="Print JSON-lines for each match."
    )
    a = p.parse_args()

    scan(
        technique=a.technique,
        status=a.status,
        errors=a.errors,
        match=a.match,
        print_matches=bool(a.print),
    )
