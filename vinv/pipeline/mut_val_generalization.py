"""
LLM-driven mutation and validation (mut_val) generalization strategy.

High-level idea:
- Replace MIC (drop literals) with LLM mutators specialized for scenarios:
  "wrong_fact", "not_inductive", and "other".
- Replace ctgDown with a lightweight validator (stubbed True for now).
- Use counterexamples (if any) and the verifier error to infer a verdict, then
  ask a verdict-specific mutator to generalize minimally while preserving
  semantics and not changing executable code or pre/post conditions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from loguru import logger
from veval import EvalScore, VerusError, VEval

from vinv.config import MUT_RANKING_MODE
from vinv.gen.client import (
    request_prompt_multi_response,
    request_prompt_one,
)
from vinv.gen.prompt_utils import render_prompt
from vinv.pipeline.counter_example import CounterExample
from vinv.pipeline.parser_utils import (
    error_inside_loop,
    extract_loop_for_error,
    extract_loop_for_id,
    read_loop_id_from_extracted,
)
from vinv.pipeline.trajectory import recorder
from vinv.pipeline.validator_extracted import validate_blocking_list_extracted
from vinv.utils import check_status, extract_rs_code_from_response
from vinv.verus_utils import record_verify_status

Verdict = Literal["wrong_fact", "too_weak", "other"]

def mut_val_cex_generalization(
    proof_file: Path,
    verus_error: VerusError,
    counter_examples: Optional[List[CounterExample]],
    try_dir: Path,
    console_error_msg: str,
    original_proof_file: Path,
    diff: str,
    model: str = "gpt-4o",
) -> Optional[Path]:
    """
    Generalize from counterexamples using LLM-based mutation and lightweight validation.

    Returns a path to the repaired proof (repaired.rs) on success; otherwise None.
    Additionally, writes multiple candidate files if generated.
    """
    try:
        try_dir.mkdir(parents=True, exist_ok=True)

        proof_content = proof_file.read_text()
        original_proof_text = original_proof_file.read_text()

        # 1) Infer verdict from error and CE via LLM
        verdict, verdict_rationale = infer_verdict(
            proof_content=proof_content,
            verus_error=verus_error,
            counter_examples=counter_examples,
            console_error_msg=console_error_msg,
            try_dir=try_dir,
            model=model,
        )
        logger.info(
            f"Inferred verdict: {verdict} ({verdict_rationale}) for {verus_error.error.name} in {try_dir}"
        )
        (try_dir / "mut_val_verdict.json").write_text(
            json.dumps({"verdict": verdict, "rationale": verdict_rationale}, indent=2)
        )

        candidates: List[Tuple[str, str]] = []  # list of (code, source_candidate_id)
        # Derive attempt from try_dir name if available (e.g., try_1)
        attempt_num: Optional[int] = None
        try:
            name = try_dir.name
            if name.startswith("try_"):
                attempt_num = int(name.split("_")[-1])
        except Exception:
            attempt_num = None

        # 2) Mutate/generalize via verdict-specific mutator until we reach max_candidates
        max_candidates = 5
        mut_prompt_fn = {
            "wrong_fact": create_mutator_prompt_wrong_fact,
            "too_weak": create_mutator_prompt_too_weak,
            "other": create_mutator_prompt_other,
        }[verdict]
        # Record mutator used in this iteration
        mutator_name = verdict
        if attempt_num is not None:
            recorder.record_mutator(attempt_num, mutator_name)

        base_mut_prompt = mut_prompt_fn(
            proof_content=proof_content,
            verus_error=verus_error,
            console_error_msg=console_error_msg,
            counter_examples=counter_examples,
            original_proof=original_proof_text,
            diff=diff,
            verdict_rationale=verdict_rationale,
        )
        (try_dir / "mut_val_mutator_base_prompt.txt").write_text(base_mut_prompt)

        # Batch-generate multiple mutations and collect the first max_candidates that compile
        responses = request_prompt_multi_response(
            base_mut_prompt,
            system=render_prompt("pipeline/mut_val/batch_system.j2"),
            model=model,
            max_retry=5,
            temperature=1.0,
            num_responses=max_candidates,
            task_id=str(try_dir),
            prompt_type_id=f"mut_val_mutator_{verdict}_multi",
        )
        for i, response in enumerate(responses, start=1):
            (try_dir / f"mut_val_mutator_response_{i}.txt").write_text(response)
            code = extract_rs_code_from_response(response)
            if code:
                candidates.append((code, f"mutant_{i}"))

        if not candidates:
            logger.warning("mut_val did not produce any candidate code")

        # Persist all candidates and select the best as repaired.rs
        repaired_file = try_dir / "repaired.rs"
        # Ranking workspace
        rank_dir = try_dir / "mut_val_mutants"
        rank_dir.mkdir(parents=True, exist_ok=True)

        # Choose effective ranking mode: fall back to veval_score if error is not inside a loop
        eff_ranking_mode = (
            "veval_score"
            if MUT_RANKING_MODE == "cex_block"
            and not error_inside_loop(proof_file, verus_error)
            else MUT_RANKING_MODE
        )
        if MUT_RANKING_MODE == "cex_block" and eff_ranking_mode == "veval_score":
            logger.info(
                "No while loop detected; falling back to 'veval_score' ranking mode for mut_val."
            )

        if eff_ranking_mode == "cex_block":
            # Compile-filter and rank candidates by number of blocked CEXs
            ranking: list[dict] = []
            num_compilable_count = 0
            # Prepare baseline once: recover loop id from the original harness (or create it)
            baseline_dir = try_dir / "harness_before"
            ori_extracted_file = baseline_dir / "extracted_loop.rs"
            baseline_fn_idx: Optional[tuple[str, int]] = None
            try:
                if ori_extracted_file.exists():
                    baseline_fn_idx = read_loop_id_from_extracted(ori_extracted_file)
                elif proof_file.exists():
                    baseline_dir.mkdir(parents=True, exist_ok=True)
                    extract_loop_for_error(proof_file, verus_error, ori_extracted_file)
                    baseline_fn_idx = read_loop_id_from_extracted(ori_extracted_file)
            except Exception as e:
                raise ValueError(f"Failed to prepare baseline: {e} for {proof_file}")
            if not baseline_fn_idx:
                raise ValueError(f"Failed to read loop id from {ori_extracted_file}")
            for code, candidate_id in candidates:
                cand_dir = rank_dir / candidate_id
                cand_dir.mkdir(parents=True, exist_ok=True)

                cand_file = cand_dir / "mutant.rs"
                cand_file.write_text(code)

                # Compile check
                status_file = cand_dir / "verify_status.txt"
                record_verify_status(cand_file, status_file)
                compiles = not check_status(status_file, "compilation_error")
                verification_ok = check_status(status_file, "verification_pass")

                # Filter: skip non-compilable mutants entirely
                if not compiles:
                    logger.info(f"Skipping non-compilable mutant {cand_file}")
                    continue
                num_compilable_count += 1

                if verification_ok:
                    # Perfect: compilable and verification passed
                    repaired_file.write_text(code)
                    logger.info(f"mutant {cand_file} passed verification, returning")
                    # Attempt to compute blocked count for this selected mutant
                    selected_blocked_count = 0
                    if baseline_fn_idx and counter_examples:
                        try:
                            cand_extracted_file = cand_dir / "extracted_loop.rs"
                            fn_name, loop_index = baseline_fn_idx
                            ok = extract_loop_for_id(
                                cand_file,
                                fn_name,
                                loop_index,
                                cand_extracted_file,
                                verus_error,
                            )
                            if ok:
                                results = validate_blocking_list_extracted(
                                    repaired_extracted_file=cand_extracted_file,
                                    counter_examples=counter_examples,
                                    validation_dir=cand_dir,
                                    baseline_results_path=baseline_dir
                                    / "batch_results.json",
                                )
                                selected_blocked_count = sum(
                                    1 for r in results if bool(r.get("blocked"))
                                )
                        except Exception:
                            selected_blocked_count = 0
                    # Record mutants and selection in trajectory
                    if attempt_num is not None:
                        recorder.record_mutants(
                            attempt_num, len(candidates), num_compilable_count
                        )
                        recorder.record_selection(
                            attempt_num,
                            candidate_id=candidate_id,
                            candidate_path=str(cand_file),
                            blocked_cex=selected_blocked_count,
                        )

                blocked_count = 0
                cand_extracted_ok = False

                # Use precomputed baseline loop id to extract the same loop on mutant
                cand_extracted_file = cand_dir / "extracted_loop.rs"
                fn_name, loop_index = baseline_fn_idx
                cand_extracted_ok = extract_loop_for_id(
                    cand_file, fn_name, loop_index, cand_extracted_file, verus_error
                )
                # If extraction failed, skip blocking evaluation for this mutant
                if cand_extracted_ok and counter_examples:
                    try:
                        results = validate_blocking_list_extracted(
                            repaired_extracted_file=cand_extracted_file,
                            counter_examples=counter_examples,
                            validation_dir=cand_dir,
                            baseline_results_path=baseline_dir / "batch_results.json",
                        )
                        blocked_count = sum(
                            1 for r in results if bool(r.get("blocked"))
                        )
                    except Exception as e:
                        logger.warning(
                            f"Blocking validation failed for {cand_file}: {e}"
                        )
                else:
                    if not cand_extracted_ok:
                        logger.warning(
                            f"Extraction failed for candidate mutant {cand_file}"
                        )
                    if not counter_examples:
                        logger.warning(
                            f"No counter examples for candidate mutant {cand_file}"
                        )

                ranking.append(
                    {
                        "candidate_id": candidate_id,
                        "path": str(cand_file),
                        "compiles": compiles,
                        "verification_passed": verification_ok,
                        "extracted": cand_extracted_ok,
                        "blocked_count": max(0, blocked_count)
                        if blocked_count >= 0
                        else 0,
                        "num_cex": len(counter_examples) if counter_examples else 0,
                    }
                )

            # Sort: compilable first (already filtered), then by blocked_count desc
            ranking_sorted = sorted(
                ranking,
                key=lambda r: (
                    0 if r.get("compiles") else 1,
                    -(r.get("blocked_count") or 0),
                ),
            )
            # if all blocked_count are 0, then fallback to use veval_score
            if all(r.get("blocked_count") == 0 for r in ranking_sorted):
                logger.warning(
                    f"All blocked_count are 0, falling back to veval_score for {try_dir}"
                )
                eff_ranking_mode = "veval_score"
            # if all blocked_count are the same, then fallback to use veval_score
            elif all(
                r.get("blocked_count") == ranking_sorted[0].get("blocked_count")
                for r in ranking_sorted
            ):
                logger.warning(
                    f"All blocked_count are the same, falling back to veval_score for {try_dir}"
                )
                eff_ranking_mode = "veval_score"
            (try_dir / "mut_val_ranking.json").write_text(
                json.dumps(ranking_sorted, indent=2)
            )

            logger.info(f"{len(ranking_sorted)} compilable mutants found")

            if attempt_num is not None:
                recorder.record_mutants(
                    attempt_num, len(candidates), num_compilable_count
                )

            # Choose top-ranked compilable candidate if any; otherwise fallback to original proof
            top = ranking_sorted[0] if ranking_sorted else None
            if top is not None:
                repaired_file.write_text(Path(top["path"]).read_text())
                if attempt_num is not None:
                    recorder.record_selection(
                        attempt_num,
                        candidate_id=top.get("candidate_id"),
                        candidate_path=top.get("path"),
                        blocked_cex=int(top.get("blocked_count") or 0),
                    )
            else:
                logger.warning(
                    "mut_val: no compilable mutants; falling back to the first one"
                )
                repaired_file.write_text(candidates[0][0])
                if attempt_num is not None:
                    # Unknown blocked count in this fallback path
                    recorder.record_selection(
                        attempt_num,
                        candidate_id=candidates[0][1],
                        candidate_path=str((rank_dir / candidates[0][1] / "mutant.rs")),
                        blocked_cex=0,
                    )

            return repaired_file

        if eff_ranking_mode == "veval_score":
            # Directly rank by VEval score; do not pre-filter non-compilable candidates
            ranking_objs: list[tuple] = []  # (EvalScore, meta_dict)
            num_compilable_count = 0
            for code, candidate_id in candidates:
                cand_dir = rank_dir / candidate_id
                cand_dir.mkdir(parents=True, exist_ok=True)

                cand_file = cand_dir / "mutant.rs"
                cand_file.write_text(code)

                try:
                    veval = VEval(code, logger)
                    score = veval.eval_and_get_score()
                except Exception as e:
                    logger.warning(f"VEval failed for {cand_file}: {e}")
                    # Worst-case score if evaluation fails

                    score = EvalScore.get_worst_score()

                if not bool(score.compilation_error):
                    num_compilable_count += 1

                # Immediate success
                if hasattr(score, "is_correct") and score.is_correct():
                    repaired_file.write_text(code)
                    if attempt_num is not None:
                        recorder.record_mutants(
                            attempt_num, len(candidates), num_compilable_count
                        )
                        recorder.record_selection(
                            attempt_num,
                            candidate_id=candidate_id,
                            candidate_path=str(cand_file),
                            blocked_cex=0,
                        )
                    return repaired_file

                meta = {
                    "candidate_id": candidate_id,
                    "path": str(cand_file),
                    "compilation_error": bool(score.compilation_error),
                    "verified": int(score.verified),
                    "errors": int(score.errors),
                    "verus_errors": int(score.verus_errors),
                    "score_str": str(score),
                }
                ranking_objs.append((score, meta))

            # Sort by VEval score descending (best first)
            ranking_objs.sort(key=lambda t: t[0], reverse=True)
            ranking_sorted = [meta for _, meta in ranking_objs]
            (try_dir / "mut_val_ranking.json").write_text(
                json.dumps(ranking_sorted, indent=2)
            )

            logger.info(
                f"{len(ranking_sorted)} evaluated mutants (ranked by VEval score)"
            )

            if attempt_num is not None:
                recorder.record_mutants(
                    attempt_num, len(candidates), num_compilable_count
                )

            # Choose top-ranked candidate if any; otherwise fallback to the first candidate
            top = ranking_sorted[0] if ranking_sorted else None
            if top is not None:
                repaired_file.write_text(Path(top["path"]).read_text())
                if attempt_num is not None:
                    recorder.record_selection(
                        attempt_num,
                        candidate_id=top.get("candidate_id"),
                        candidate_path=top.get("path"),
                        blocked_cex=0,
                    )
            else:
                logger.warning(
                    "mut_val: no evaluated compilable mutants; falling back to the first mutant"
                )
                repaired_file.write_text(candidates[0][0])
                if attempt_num is not None:
                    recorder.record_selection(
                        attempt_num,
                        candidate_id=candidates[0][1],
                        candidate_path=str((rank_dir / candidates[0][1] / "mutant.rs")),
                        blocked_cex=0,
                    )
        (try_dir / "mut_val_candidates_meta.json").write_text(
            json.dumps(
                {
                    "verdict": verdict,
                    "num_candidates": len(candidates),
                    "sources": [candidate_id for _, candidate_id in candidates],
                },
                indent=2,
            )
        )
        logger.info(
            f"Generated mut_val repaired proof with {len(candidates)} candidates: {repaired_file}"
        )
        return repaired_file

    except Exception as e:
        logger.error(f"Failed to perform mut_val generalization: {e}")
        return None


# --------------------------- Heuristics & Prompts ----------------------------


def infer_verdict(
    proof_content: str,
    verus_error: VerusError,
    counter_examples: Optional[List[CounterExample]],
    console_error_msg: str,
    try_dir: Path,
    model: str,
) -> Tuple[Verdict, str]:
    """
    Use an LLM to infer the verdict: "wrong_fact" | "too_weak" | "other".

    Encodes domain knowledge:
    - InvFailFront => likely wrong_fact
    - InvFailEnd => could be wrong_fact or too_weak (needs strengthening)
    - PreCondFailVecLen / PreCondFail / ArithmeticFlow => often too_weak due to missing bounds
    - wrong_fact CEs are real reachable states; too_weak CEs are spurious and should be blocked
    """
    try_dir.mkdir(parents=True, exist_ok=True)

    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)

    prompt = render_prompt(
        "pipeline/mut_val/verdict_user.j2",
        proof_content=proof_content,
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        cex_info=cex_info,
    )

    (try_dir / "mut_val_verdict_prompt.txt").write_text(prompt)
    response = request_prompt_one(
        prompt,
        system=render_prompt("pipeline/mut_val/verdict_system.j2"),
        model=model,
        max_retry=5,
        temperature=1.0,
        task_id=str(try_dir),
        prompt_type_id="mut_val_verdict",
    )
    (try_dir / "mut_val_verdict_response.txt").write_text(response)

    verdict, rationale = parse_verdict_response(response)
    return verdict, rationale


def create_mutator_prompt_wrong_fact(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
    original_proof: str,
    diff: str,
    verdict_rationale: Optional[str] = None,
) -> str:
    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)
    return render_prompt(
        "pipeline/mut_val/wrong_fact_user.j2",
        proof_content=proof_content,
        verdict_rationale=verdict_rationale or "",
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        cex_info=cex_info,
        original_proof=original_proof,
        diff=diff,
    )


def create_mutator_prompt_too_weak(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
    original_proof: str,
    diff: str,
    verdict_rationale: Optional[str] = None,
) -> str:
    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)
    return render_prompt(
        "pipeline/mut_val/too_weak_user.j2",
        proof_content=proof_content,
        verdict_rationale=verdict_rationale or "",
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        cex_info=cex_info,
        original_proof=original_proof,
        diff=diff,
    )


def create_mutator_prompt_other(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
    original_proof: str,
    diff: str,
    verdict_rationale: Optional[str] = None,
) -> str:
    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)
    return render_prompt(
        "pipeline/mut_val/other_user.j2",
        proof_content=proof_content,
        verdict_rationale=verdict_rationale or "",
        error_type=verus_error.error.name,
        error_message=verus_error.get_text(),
        console_error_msg=console_error_msg,
        cex_info=cex_info,
        original_proof=original_proof,
        diff=diff,
    )


# ------------------------------ Validators ----------------------------------


def is_directionally_correct(verdict: Verdict) -> bool:
    """Placeholder: always returns True. Later, check weakening/strengthening by verdict."""
    return True


def blocks_counterexample(code: str, try_dir: Path, candidate_id: str) -> bool:
    """
    Lightweight validator: currently filters out candidates that cause compilation errors.
    Future: also check that the previous counterexamples are blocked.
    """
    try:
        veval = VEval(code, logger)
        score = veval.eval_and_get_score()
        return not score.compilation_error
    except Exception:
        return False


# ------------------------------ Utilities -----------------------------------


def parse_verdict_response(text: str) -> Tuple[Verdict, str]:
    """Parse JSON verdict from LLM response; robust to surrounding text."""
    try:
        obj = json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(text[start : end + 1])
            except Exception:
                return "other", "Could not parse verdict JSON; defaulting to 'other'."
        else:
            return "other", "No JSON found in verdict response; defaulting to 'other'."

    verdict_raw = str(obj.get("verdict", "other")).strip().lower()
    rationale = str(obj.get("rationale", "")).strip()

    if verdict_raw in ("wrong_fact", "wrongfact"):
        return "wrong_fact", rationale or "Classified as wrong_fact by LLM."
    if verdict_raw in ("too_weak", "too weak", "not_inductive", "not-inductive"):
        return "too_weak", rationale or "Classified as too_weak by LLM."
    return "other", rationale or "Classified as other by LLM."
