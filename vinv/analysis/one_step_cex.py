import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fire import Fire


def _json_load(p: Path) -> Optional[Any]:
    try:
        if p and p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None


def _count_generated_cex(try_dir: Path) -> int:
    cex_file = try_dir / "cex" / "generated_z3_cex.json"
    data = _json_load(cex_file)
    if isinstance(data, list):
        return len(data)
    return 0


def _count_validated_cex(try_dir: Path) -> int:
    # Baseline validation results live under harness_before/batch_results.json
    res_file = try_dir / "harness_before" / "batch_results.json"
    results = _json_load(res_file)
    if not isinstance(results, list):
        return 0
    count = 0
    for r in results:
        if not isinstance(r, dict):
            continue
        if r.get("compilation_error"):
            continue
        if bool(r.get("detected")) and not bool(r.get("verification_passed")):
            count += 1
    return count


def _collect_mutant_blocking(try_dir: Path) -> List[Dict[str, Any]]:
    mutants_root = try_dir / "mut_val_mutants"
    out: List[Dict[str, Any]] = []
    if not mutants_root.is_dir():
        return out
    for sub in sorted([p for p in mutants_root.iterdir() if p.is_dir()]):
        batch_path = sub / "batch_blocking_results.json"
        results = _json_load(batch_path)
        if not isinstance(results, list):
            # If missing, still record the mutant with zeroes
            out.append(
                {
                    "candidate_id": sub.name,
                    "blocked_count": 0,
                    "num_cex": 0,
                    "results_path": str(batch_path),
                }
            )
            continue
        blocked = sum(
            1 for r in results if isinstance(r, dict) and bool(r.get("blocked"))
        )
        out.append(
            {
                "candidate_id": sub.name,
                "blocked_count": int(blocked),
                "num_cex": int(len(results)),
                "results_path": str(batch_path),
            }
        )
    return out


def analyze_try_dir(
    try_dir: str, out: Optional[str] = None, quiet: bool = False
) -> Dict[str, Any]:
    td = Path(try_dir)
    summary: Dict[str, Any] = {
        "try_dir": str(td),
        "num_cex_generated": _count_generated_cex(td),
        "num_cex_validated": _count_validated_cex(td),
        "mutants": _collect_mutant_blocking(td),
    }
    summary["num_mutants"] = (
        len(summary["mutants"]) if isinstance(summary.get("mutants"), list) else 0
    )

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    if not quiet:
        # Also print to stdout for convenience
        print(json.dumps(summary, indent=2))
    return summary


def main(try_dir: str, out: Optional[str] = None, quiet: bool = False):
    """
    Analyze a single CEX repair attempt directory (try_*).

    Inputs under try_dir expected (best-effort, missing files are tolerated):
    - cex/generated_z3_cex.json               -> number of CEX generated
    - harness_before/batch_results.json       -> number of CEX validated (detected && !verification_passed)
    - mut_val_mutants/*/batch_blocking_results.json -> per-mutant blocked counts

    Example:
        python -m vinv.analysis.one_step_cex --try_dir /path/to/try_1 --out /tmp/cex_stats.json
    """
    return analyze_try_dir(try_dir, out, quiet)


if __name__ == "__main__":
    Fire(main)
