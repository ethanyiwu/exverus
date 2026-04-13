import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fire import Fire
from loguru import logger

# autoverus imports
from veval import VerusErrorType, VEval

from vinv.config import INV_INJECT_RESULTS_DIR
from vinv.data.cherrypick import get_all_vb_proofs
from vinv.gen.client import request_prompt_one
from vinv.gen.prompt_utils import make_unified_diff, render_prompt
from vinv.proof import OneStepProofFile, ProofFile
from vinv.utils import extract_rs_code_from_response
from vinv.verus_utils import record_verify_status, verify_with_verus

INJECT_TYPES = {
    "strengthen_invariant": {
        "expected_error_type": VerusErrorType.InvFailFront,
        "template": "data/invariant_inject/strengthen_invariant_user.j2",
    },
    "weaken_invariant": {
        "expected_error_type": VerusErrorType.InvFailEnd,
        "template": "data/invariant_inject/weaken_invariant_user.j2",
    },
    "add_invariant": {
        "expected_error_type": VerusErrorType.InvFailFront,
        "template": "data/invariant_inject/add_invariant_user.j2",
    },
    "remove_invariant": {
        "expected_error_type": VerusErrorType.InvFailEnd,
        "template": "data/invariant_inject/remove_invariant_user.j2",
    },
}


def _normalize_line(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def check_one_invariant_diff(
    original: str, modified: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Heuristically check whether the diff changes at most one invariant block and nothing else.

    Returns (ok, details).
    - ok: True if only one invariant site was changed and no non-invariant code/spec was modified.
    - details: statistics for reporting.
    """
    u = list(
        difflib.unified_diff(
            original.splitlines(), modified.splitlines(), n=3, lineterm=""
        )
    )
    changed_groups = 0
    non_invariant_changes = 0
    current_invariant_block_has_change = False
    in_invariant_context = False

    # Walk through diff hunks
    for line in u:
        if line.startswith("@@"):
            # Close previous invariant block if it had changes
            if current_invariant_block_has_change:
                changed_groups += 1
                current_invariant_block_has_change = False
            in_invariant_context = False
            continue
        if line.startswith(" "):
            # context line
            text = line[1:]
            if "invariant" in text:
                in_invariant_context = True
            if text.strip() == "{":
                in_invariant_context = False
            continue
        if line.startswith("+") or line.startswith("-"):
            text = line[1:]
            # ignore pure whitespace changes
            if _normalize_line(text) == "":
                continue
            is_invariant_related = in_invariant_context or ("invariant" in text)
            if is_invariant_related:
                current_invariant_block_has_change = True
            else:
                non_invariant_changes += 1

    # finalize last block
    if current_invariant_block_has_change:
        changed_groups += 1

    ok = changed_groups == 1 and non_invariant_changes == 0
    details = {
        "changed_invariant_groups": changed_groups,
        "non_invariant_changes": non_invariant_changes,
        "unified_diff": "\n".join(u),
    }
    return ok, details


def check_one_invariant_diff_structural(
    original_file: Path, original: str, modified: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Structural check using parsed invariant ranges from the original file.
    Ensures all changes lie strictly within exactly one invariant block and
    nowhere else.
    """
    try:
        try:
            proof = ProofFile(original_file)
        except Exception:
            # Fallback for files outside verified/unverified layout
            proof = OneStepProofFile(original_file)
        inv_map = proof.parse_invariants()  # func_id -> List[InvariantEntry]
        inv_ranges: list[tuple[int, int]] = []  # 0-based inclusive ranges
        for _, inv_list in inv_map.items():
            for entry in inv_list:
                # invariant_entry_start/end are 1-based inclusive indices of predicate lines
                start0 = int(entry.invariant_entry_start) - 1
                end0 = int(entry.invariant_entry_end) - 1
                inv_ranges.append((start0, end0))

        orig_lines = original.splitlines()
        mod_lines = modified.splitlines()

        from difflib import SequenceMatcher

        sm = SequenceMatcher(a=orig_lines, b=mod_lines, autojunk=False)
        changed_blocks_indices: set[int] = set()
        non_invariant_changes = 0

        def _range_inside_one_inv(i1: int, i2: int) -> Optional[int]:
            # i1, i2 are 0-based half-open [i1, i2)
            if i1 >= i2:
                return None
            for idx, (s, e) in enumerate(inv_ranges):
                if i1 >= s and (i2 - 1) <= e:
                    return idx
            return None

        def _insert_pos_in_inv(i: int) -> Optional[int]:
            # insertion happens at position i in original. Allow insertion
            # within [s, e+1] so adding a predicate at end is accepted.
            for idx, (s, e) in enumerate(inv_ranges):
                if i >= s and i <= e + 1:
                    return idx
            return None

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace" or tag == "delete":
                inv_idx = _range_inside_one_inv(i1, i2)
                if inv_idx is None:
                    non_invariant_changes += 1
                else:
                    changed_blocks_indices.add(inv_idx)
            elif tag == "insert":
                inv_idx = _insert_pos_in_inv(i1)
                if inv_idx is None:
                    non_invariant_changes += 1
                else:
                    changed_blocks_indices.add(inv_idx)
            else:
                non_invariant_changes += 1

        ok = (len(changed_blocks_indices) == 1) and (non_invariant_changes == 0)
        details = {
            "changed_invariant_groups": len(changed_blocks_indices),
            "non_invariant_changes": non_invariant_changes,
            "unified_diff": "\n".join(
                difflib.unified_diff(orig_lines, mod_lines, n=3, lineterm="")
            ),
        }
        return ok, details
    except Exception as e:
        # Fallback to heuristic if structural parsing fails
        logger.warning(
            f"Structural invariant diff check failed: {e}. Falling back to heuristic."
        )
        return check_one_invariant_diff(original, modified)


def run_injection_once(
    proof_file: Path,
    inject_type: str,
    model: str,
    out_dir: Path,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    original_code = proof_file.read_text()
    (out_dir / "gt.rs").write_text(original_code)

    user_prompt = render_prompt(
        INJECT_TYPES[inject_type]["template"],
        proof=original_code,
    )
    system_prompt = render_prompt("data/invariant_inject/system.j2")
    response = request_prompt_one(
        user_prompt,
        system=system_prompt,
        model=model,
        max_retry=5,
        temperature=0.2,
        task_id=str(out_dir),
        prompt_type_id=f"invariant_inject_{inject_type}",
    )

    (out_dir / "conversation.json").write_text(
        json.dumps(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": response},
            ],
            indent=2,
        )
    )
    (out_dir / "response.txt").write_text(response)

    injected_code = extract_rs_code_from_response(response)
    if not injected_code:
        raise ValueError(f"Failed to extract Rust code for {inject_type} in {out_dir}")
    injected_path = out_dir / "injected.rs"
    injected_path.write_text(injected_code)

    # Diff
    diff_text = make_unified_diff(original_code, injected_code)
    (out_dir / "diff.diff").write_text(diff_text)

    # Verify and collect outputs
    stdout_file = out_dir / "verus_out.txt"
    stderr_file = out_dir / "verus_err.txt"
    verify_with_verus(
        proof_file=injected_path, stdout_file=stdout_file, stderr_file=stderr_file
    )
    verify_status_file = out_dir / "verify_status.txt"
    record_verify_status(injected_path, verify_status_file, override=True)
    status_str = verify_status_file.read_text().strip()
    is_buggy = status_str in {"verification_error", "compilation_error"}

    # VEval for error extraction
    veval = VEval(injected_code, logger)
    veval.eval_and_get_score()
    errors = veval.get_failures()
    error_types = [e.error.name for e in errors] if errors else []
    verus_out = getattr(veval, "verus_out", "")
    rustc_out = getattr(veval, "rustc_out", "")
    (out_dir / "veval_verus_out.txt").write_text(verus_out or "")
    (out_dir / "veval_rustc_out.txt").write_text(rustc_out or "")

    # Check one-invariant diff (structural, with heuristic fallback)
    one_inv_ok, diff_details = check_one_invariant_diff_structural(
        proof_file, original_code, injected_code
    )
    (out_dir / "diff_checked.txt").write_text(diff_details.get("unified_diff", ""))

    # Check expected error type presence
    expected_type: VerusErrorType = INJECT_TYPES[inject_type]["expected_error_type"]
    expected_error_found = any(
        (getattr(e, "error", None) == expected_type) for e in (errors or [])
    )

    result: Dict[str, Any] = {
        "inject_type": inject_type,
        "expected_error_type": expected_type.name,
        "is_buggy": is_buggy,
        "verify_status": status_str,
        "one_invariant_diff": one_inv_ok,
        "changed_invariant_groups": diff_details.get("changed_invariant_groups"),
        "non_invariant_changes": diff_details.get("non_invariant_changes"),
        "expected_error_found": expected_error_found,
        "error_types": error_types,
        "verus_out_file": str(stdout_file),
        "rustc_out_file": str(stderr_file),
    }
    (out_dir / "result.json").write_text(json.dumps(result, indent=2))
    return result


def main(
    model: str = "gpt-4o",
):
    proofs = get_all_vb_proofs(with_invariant=True, use_specified_taskids=False)
    logger.info(f"Found {len(proofs)} proofs with invariants")

    for proof in proofs:
        work_dir = INV_INJECT_RESULTS_DIR / f"{model}" / proof.task_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # Run all injection types
        summary: Dict[str, Any] = {"task_id": proof.task_id, "results": {}}
        for inject_type in INJECT_TYPES.keys():
            type_dir = work_dir / inject_type
            try:
                result = run_injection_once(proof.path, inject_type, model, type_dir)
                summary["results"][inject_type] = result
            except Exception as e:
                logger.error(
                    f"Injection failed for {proof.task_id} [{inject_type}]: {e}"
                )
                summary["results"][inject_type] = {
                    "inject_type": inject_type,
                    "exception": str(e),
                }

        (work_dir / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    Fire(main)
