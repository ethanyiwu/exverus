import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fire import Fire
from veval import VerusErrorType

from vinv.config import PIPELINE_RESULTS_DIR
from vinv.data.cherrypick import get_all_vb_proofs
from vinv.utils import check_status

TARGET_STRATEGY_DIRNAME = "cex_repair_z3_mut_val_10"
MODELS_DEFAULT = ["gpt-4o", "deepseek-chat-v3.1"]
SOURCES_DEFAULT = ["CLEANED_VB", "ADDITIONAL"]


def _safe_read_text(p: Path) -> str:
    try:
        return p.read_text()
    except Exception:
        return ""


def _safe_read_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _parse_error_count(err_text: str) -> Optional[int]:
    if not err_text:
        return None
    m = re.search(
        r"verification results::\s*(\d+)\s*verified,\s*(\d+)\s*errors", err_text
    )
    if m:
        try:
            return int(m.group(2))
        except Exception:
            pass
    # fallback: count distinct "error:" lines (rough heuristic)
    count = len([ln for ln in err_text.splitlines() if ln.strip().startswith("error:")])
    return count if count > 0 else None


def _detect_error_type(err_text: str) -> Optional[VerusErrorType]:
    s = err_text.lower()
    if "invariant not satisfied at end of loop body" in s:
        return VerusErrorType.InvFailEnd
    if "invariant not satisfied before loop" in s:
        return VerusErrorType.InvFailFront
    return None


def _diff_strengthens_invariant(diff_text: str) -> bool:
    if not diff_text:
        return False
    added_lines = [
        ln
        for ln in diff_text.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    ]
    return any("invariant" in ln for ln in added_lines)


def _z3_cex_count(try_dir: Path) -> int:
    cex_file = try_dir / "cex" / "generated_z3_cex.json"
    data = _safe_read_json(cex_file)
    if isinstance(data, list):
        return len(data)
    return 0


def _validated_cex_count(batch_results_path: Path) -> int:
    data = _safe_read_json(batch_results_path)
    if not isinstance(data, list):
        return 0
    return sum(1 for r in data if bool(r.get("detected")))


def _any_blocked_in_mutants(mutants_dir: Path) -> bool:
    if not mutants_dir.is_dir():
        return False
    for sub in sorted(mutants_dir.iterdir()):
        if not sub.is_dir():
            continue
        f = sub / "batch_blocking_results.json"
        data = _safe_read_json(f)
        if isinstance(data, list):
            if any(bool(r.get("blocked")) for r in data):
                return True
    return False


def _read_repair_metadata(try_dir: Path) -> Dict[str, Optional[str]]:
    meta: Dict[str, Optional[str]] = {"error_type": None}
    rs = _safe_read_json(try_dir / "repair_status.json")
    if isinstance(rs, dict):
        et = rs.get("error_type")
        if isinstance(et, str):
            meta["error_type"] = et
    mv = _safe_read_json(try_dir / "mut_val_verdict.json")
    if isinstance(mv, dict):
        v = mv.get("verdict")
        r = mv.get("rationale")
        if isinstance(v, str):
            meta["mut_val_verdict"] = v
        if isinstance(r, str):
            meta["mut_val_rationale"] = r
    return meta


def find_interesting_cases(
    models: List[str] = MODELS_DEFAULT,
    sources: List[str] = SOURCES_DEFAULT,
    max_errors_before_fix: int = 2,
) -> List[Dict[str, str]]:
    """
    Scan completed runs and return one-step fixes under cex_repair_z3_mut_val_10
    that satisfy:
      1) task finally repaired
      2) before-repair errors <= max_errors_before_fix
      3) if InvFailEnd, diff adds/modifies an invariant
      4) multiple Z3 counterexamples generated
      5) counterexamples validated in harness_before/batch_results.json
      6) at least one mutant blocks some CE in mut_val_mutants/*/batch_blocking_results.json
    """
    results: List[Dict[str, str]] = []

    # Iterate over all proofs we know about to bound the search space
    proofs = []
    for src in sources:
        proofs.extend(get_all_vb_proofs(source=src, use_specified_taskids=False))

    # Index proofs by source for path construction
    by_source: Dict[str, List] = {src: [] for src in sources}
    for p in proofs:
        by_source.setdefault(p.source, []).append(p)

    for model in models:
        for src in sources:
            for proof in by_source.get(src, []):
                work_dir = PIPELINE_RESULTS_DIR / model / src / proof.full_id
                strat_dir = work_dir / TARGET_STRATEGY_DIRNAME
                gen_dir = strat_dir / "gen_0"
                if not gen_dir.is_dir():
                    continue

                try_dirs = sorted(
                    [
                        d
                        for d in gen_dir.iterdir()
                        if d.is_dir() and d.name.startswith("try_")
                    ]
                )
                if not try_dirs:
                    continue

                for try_dir in try_dirs:
                    # 1) finally repaired
                    repaired_ok = False
                    status_file = strat_dir / "cex_repair_status.txt"
                    if status_file.is_file():
                        repaired_ok = check_status(status_file, "verification_pass")
                    else:
                        rvf = try_dir / "repaired_verify_status.txt"
                        if rvf.is_file():
                            repaired_ok = check_status(rvf, "verification_pass")
                    if not repaired_ok:
                        continue

                    # 2) errors before repair <= threshold
                    err_txt = _safe_read_text(try_dir / "input_err.txt")
                    err_count = _parse_error_count(err_txt)
                    if err_count is None or err_count > max_errors_before_fix:
                        continue

                    # error type and diff check for InvFailEnd
                    err_ty = _detect_error_type(err_txt)
                    if err_ty == VerusErrorType.InvFailEnd:
                        diff_ok = _diff_strengthens_invariant(
                            _safe_read_text(try_dir / "diff_before_after.diff")
                        )
                        if not diff_ok:
                            continue

                    # 4) multiple z3 cex
                    if _z3_cex_count(try_dir) < 2:
                        continue

                    # 5) validated in baseline harness
                    batch_results = try_dir / "harness_before" / "batch_results.json"
                    if _validated_cex_count(batch_results) < 1:
                        continue

                    # 6) at least one mutant blocks some CE
                    mutants_dir = try_dir / "mut_val_mutants"
                    if not _any_blocked_in_mutants(mutants_dir):
                        continue

                    meta = _read_repair_metadata(try_dir)
                    out = {
                        "model": model,
                        "source": src,
                        "proof_id": proof.full_id,
                        "try_dir": str(try_dir),
                    }
                    out.update({k: v for k, v in meta.items() if v is not None})
                    results.append(out)

    return results


def collect_cases_and_reasons(
    models: List[str] = MODELS_DEFAULT,
    sources: List[str] = SOURCES_DEFAULT,
    max_errors_before_fix: int = 2,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Same as find_interesting_cases, but also collect per-task rejection reasons.
    Returns (matches, rejections).
    """
    matches: List[Dict[str, str]] = []
    rejections: List[Dict[str, str]] = []

    proofs = []
    for src in sources:
        proofs.extend(get_all_vb_proofs(source=src, use_specified_taskids=False))

    by_source: Dict[str, List] = {src: [] for src in sources}
    for p in proofs:
        by_source.setdefault(p.source, []).append(p)

    for model in models:
        for src in sources:
            for proof in by_source.get(src, []):
                reasons: List[str] = []
                work_dir = PIPELINE_RESULTS_DIR / model / src / proof.full_id
                strat_dir = work_dir / TARGET_STRATEGY_DIRNAME
                gen_dir = strat_dir / "gen_0"
                if not gen_dir.is_dir():
                    reasons.append("missing gen_0 directory for target strategy")
                    rejections.append(
                        {
                            "model": model,
                            "source": src,
                            "proof_id": proof.full_id,
                            "reasons": reasons,
                        }
                    )
                    continue

                try_dirs = sorted(
                    [
                        d
                        for d in gen_dir.iterdir()
                        if d.is_dir() and d.name.startswith("try_")
                    ]
                )
                if len(try_dirs) == 0:
                    reasons.append("no try_* directory (no attempt recorded)")
                    rejections.append(
                        {
                            "model": model,
                            "source": src,
                            "proof_id": proof.full_id,
                            "reasons": reasons,
                        }
                    )
                    continue
                # Evaluate each try; accept any passing try; otherwise record per-try reasons
                any_match = False
                per_try_reasons: List[str] = []
                for try_dir in try_dirs:
                    t_reasons: List[str] = []

                    # repaired?
                    status_file = strat_dir / "cex_repair_status.txt"
                    repaired_ok = False
                    if status_file.is_file():
                        repaired_ok = check_status(status_file, "verification_pass")
                    else:
                        rvf = try_dir / "repaired_verify_status.txt"
                        if rvf.is_file():
                            repaired_ok = check_status(rvf, "verification_pass")
                    if not repaired_ok:
                        t_reasons.append("not repaired (verification did not pass)")

                    # error count
                    err_txt = _safe_read_text(try_dir / "input_err.txt")
                    err_count = _parse_error_count(err_txt)
                    if err_count is None:
                        t_reasons.append(
                            "could not parse error count from input_err.txt"
                        )
                    elif err_count > max_errors_before_fix:
                        t_reasons.append(
                            f"too many errors before fix: {err_count} > {max_errors_before_fix}"
                        )

                    # InvFailEnd diff check
                    err_ty = _detect_error_type(err_txt)
                    if err_ty == VerusErrorType.InvFailEnd:
                        if not _diff_strengthens_invariant(
                            _safe_read_text(try_dir / "diff_before_after.diff")
                        ):
                            t_reasons.append(
                                "InvFailEnd but diff does not add/modify invariant"
                            )

                    # z3 cex count
                    z3_count = _z3_cex_count(try_dir)
                    if z3_count < 2:
                        t_reasons.append(f"too few z3 counterexamples: {z3_count}")

                    # validation
                    val_count = _validated_cex_count(
                        try_dir / "harness_before" / "batch_results.json"
                    )
                    if val_count < 1:
                        t_reasons.append(
                            "no validated counterexamples in batch_results.json"
                        )

                    # blocking mutants
                    if not _any_blocked_in_mutants(try_dir / "mut_val_mutants"):
                        t_reasons.append("no mutants blocked any counterexample")

                    if not t_reasons:
                        meta = _read_repair_metadata(try_dir)
                        out = {
                            "model": model,
                            "source": src,
                            "proof_id": proof.full_id,
                            "try_dir": str(try_dir),
                        }
                        out.update({k: v for k, v in meta.items() if v is not None})
                        matches.append(out)
                        any_match = True
                    else:
                        per_try_reasons.append(
                            f"{try_dir.name}: {', '.join(t_reasons)}"
                        )

                if not any_match:
                    rejections.append(
                        {
                            "model": model,
                            "source": src,
                            "proof_id": proof.full_id,
                            "reasons": per_try_reasons
                            or ["no try satisfied all criteria"],
                        }
                    )

    return matches, rejections


def main(
    models: str = ",".join(MODELS_DEFAULT),
    sources: str = ",".join(SOURCES_DEFAULT),
    max_errors_before_fix: int = 5,
    print_json: bool = True,
    include_rejections: bool = False,
):
    models_list = [m.strip() for m in models.split(",") if m.strip()]
    sources_list = [s.strip() for s in sources.split(",") if s.strip()]
    matches, rejections = collect_cases_and_reasons(
        models=models_list,
        sources=sources_list,
        max_errors_before_fix=max_errors_before_fix,
    )
    if print_json:
        if include_rejections:
            print(json.dumps({"matches": matches, "rejections": rejections}, indent=2))
        else:
            print(json.dumps(matches, indent=2))
    else:
        print("Matches:")
        for m in matches:
            print(f"[{m['model']}/{m['source']}] {m['proof_id']} -> {m['try_dir']}")
        if include_rejections:
            print("\nRejections:")
            for r in rejections:
                print(
                    f"[{r['model']}/{r['source']}] {r['proof_id']} :: reasons={'; '.join(r.get('reasons', []))}"
                )


if __name__ == "__main__":
    Fire(main)
