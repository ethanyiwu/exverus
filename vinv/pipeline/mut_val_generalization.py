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
    request_conversation_multi_response,
    request_conversation_one,
)
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

COMMON_RULES = """
CRITICAL RULES - NEVER MODIFY:
1. Any executable code (logic, control flow, variables, expressions, statements)
2. Function signatures or parameters
3. Requires/ensures function specifications
4. Return values or types
5. NEVER use data type casts (e.g., `i as usize`, `i as int`) in loop invariants
6. Never use `old` in the loop invariant
"""


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
        system_prompt = """
        You are an expert in Rust/Verus invariants. Propose minimal, semantically-meaningful mutations to
        invariants/assertions only that address the counterexamples. Keep pre/post and executable code
        unchanged. Output the COMPLETE fixed code in a single fenced Rust block (in the end) and a brief
        explanation of what you changed and why.
        CRITICAL RULES - NEVER MODIFY:
        1. Any executable code (logic, control flow, expressions, statements)
        2. Function signatures or parameters
        3. Requires/ensures function specifications
        4. Return values or types
        5. Never use data type casts (e.g., `i as usize`, `i as int`) in loop invariants
        6. Never use `old` in the loop invariant
        7. If there are counterexamples provided, please show how counterexamples help you come up with the mutation.
        Note:
        1. When `#[verifier::loop_isolation(false)]` is specified, the loop is not isolated and the invariants/assertions are shared between loops, thus if a correct invariant got "invariant not satisfied before loop" error, maybe some dependent invariant in prior loops is missing and should be added.
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": base_mut_prompt},
        ]

        responses = request_conversation_multi_response(
            messages,
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

    knowledge = (
        "- If the error is `invariant not satisfied before loop`, the invariant is likely a wrong fact and needs to be weakened or removed. Or it is missing a fact that was not explicitly stated previously, e.g., not stated in prior loops.\n"
        "- If the error is `invariant not satisfied at end of loop body`, the invariant could be a wrong fact or correct but too weak; propose strengthening if plausible or replace it with a correct one.\n"
        "- PreCondFailVecLen, PreCondFail, and ArithmeticFlow often indicate missing bounds over array indices or variables, suggesting the invariant is too weak.\n"
        "- If all invariants are correct, the error is likely other.\n"
        "- If an invariant is a correct fact but still got `invariant not satisfied before loop` error, it's possible that an dependent invariant/fact is not stated in prior loops and should be added.\n"
        "- `old` is not allowed in the loop invariant.\n"
        "- For errors not related to invariants or bound overflow/underflow, the error is likely other.\n"
        "- For `other` error, when the invariants look correct, we likely need to add/fix some assertions to fix it."
        "- The provided counterexamples are not necessarily reachable states, they could be spurious states that satisfy the invariants but fail the invariants after one iteration."
        "- No counterexamples provided does not mean there are no counterexamples."
    )

    prompt = f"""
# Verdict Inference for Invariant Repair

Classify the failure into one of: wrong_fact, too_weak, other.

Given:
- Proof:
```rust
{proof_content}
```
- Error Type: {verus_error.error.name}
- Error Message: {verus_error.get_text()}
- Console output:
```
{console_error_msg}
```

Counterexamples (if any):
```
{cex_info}
```

Please reason step by step on whether the counterexamples are reachable states or spurious states.

Domain knowledge:
{knowledge}

Instructions:
1) Decide whether the invariant/assertion is a wrong_fact, too_weak, or other. Use the knowledge above.
2) Consider CE reachability: real/reachable => wrong_fact; spurious => too_weak.
3) InvFailFront is usually wrong_fact (but not always); InvFailEnd can be either wrong_fact or too_weak.
4) PreCondFailVecLen, PreCondFail, and ArithmeticFlow usually imply too_weak (missing bounds).
5) If there are counterexamples provided, please show how counterexamples help you decide the verdict.

Output strictly as JSON:
{{"verdict": "wrong_fact|too_weak|other", "rationale": "..."}}
"""

    (try_dir / "mut_val_verdict_prompt.txt").write_text(prompt)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert in Rust/Verus verification. Infer classification labels precisely and respond only with the requested JSON."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response = request_conversation_one(
        messages,
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
    examples = """
Example 1 (Correcting an off-by-one in a quantifier):
Before: invariant forall|k: int| 0 <= k < i ==> a[k] > 0
After:  invariant forall|k: int| 0 <= k < i-1 ==> a[k] > 0
Why: The counterexample shows the property fails for k == i-1. The invariant is only true for the elements *before* the current one being processed.

Example 2 (Relax strict bound):
Before: invariant sum <= target
After:  invariant sum <= target + 1
Why: Off-by-one at initialization; relax by minimal constant allowed by logic.

Example 3 (Drop domain-mismatched clause):
Before: invariant xs.len() == n && n >= 0
After:  invariant n >= 0
Why: xs.len() equals array length not modeled; clause contradicts setup.

Example 4 (Weaken implication guard):
Before: invariant a > 0 ==> b/a >= c
After:  invariant a != 0 ==> b/a >= c
Why: CE shows a<0 but nonzero is sufficient for division safety used here.

Example 5 (Adjusting a quantifier's range to match logic):
Before: invariant forall|j: nat| 0 <= j < i ==> processed(items[j])
After:  invariant forall|j: nat| start <= j < i ==> processed(items[j])
Why: The loop starts processing from a non-zero offset `start`. The counterexample showed a failure for `j < start`, where items are not yet processed. The invariant must reflect the actual range of work.
"""

    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)

    prompt = f"""
# Mutator: wrong_fact

Task: Remove or minimally weaken invariants/assertions that are contradicted by the counterexample(s).
Do not change executable code or requires/ensures. Keep changes minimal and sound.

{COMMON_RULES}

Few-shot mutations:
{examples}

Current proof:
```rust
{proof_content}
```

Inferred verdict rationale:
{verdict_rationale or ''}

Error: {verus_error.error.name} — {verus_error.get_text()}
Console output:
```
{console_error_msg}
```
Counterexamples:
```
{cex_info}
```
Original (reference, DO NOT change code/specs):
```rust
{original_proof}
```
Unified diff (reference for unintended edits):
```
{diff}
```

Output the fixed proof with updated invariants, wrapped in a single Rust block ```rust <code>``` in the end and a brief explanation of what you changed and why.
"""
    return prompt


def create_mutator_prompt_too_weak(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
    original_proof: str,
    diff: str,
    verdict_rationale: Optional[str] = None,
) -> str:
    examples = """
Example 1 (Add a bound needed for an operation inside the loop):
Before: invariant 0 <= i <= N
After:  invariant 0 <= i <= N && N < 1024
Why: An operation inside the loop fails because `N` can be too large, causing an overflow or assertion failure. A function precondition bounds it, and this fact must be carried into the invariant to be available inside the loop. The `N` could come from a function precondition but the invariant must restate it explicitly to be available inside the loop.

Example 2 (Index coupling/progress):
Before: invariant 0 <= i && i <= n
After:  invariant 0 <= i && i <= n && j <= i
Why: Ensure the inner index j never exceeds the processed prefix; blocks the CE.

Example 3 (Update quantifier range to match logic):
Before: invariant forall|j: nat| start <= j < i ==> processed(items[j])
After:  invariant forall|j: nat| 0 <= j < i ==> processed(items[j])
Why: The loop starts processing from a non-zero offset `start`. The invariant must reflect the actual range of work. While `forall|j: nat| start <= j < i ==> processed(items[j])` is correct, it is not inductive and strong enough to preserve itself.

Example 4 (Couple loop variables to maintain a key relationship):
Before: invariant 0 <= read_idx <= v.len() && 0 <= write_idx <= v.len()
After:  invariant 0 <= write_idx <= read_idx <= v.len()
Why: The algorithm's correctness depends on the write pointer never overtaking the read pointer. This coupling `write_idx <= read_idx` was missing, leading to a spurious counterexample.

Example 5 (Connect a boolean flag to an existential property):
Before: invariant 0 <= i <= v.len()
After:  invariant 0 <= i <= v.len() && (found ==> exists|k: int| 0 <= k < i && v[k] == target)
Why: To prove the postcondition, the verifier must know *why* the `found` flag is true. This clause strengthens the invariant by linking the flag to the property it represents: that the target has been seen in the processed prefix.
"""

    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)

    prompt = f"""
# Mutator: too_weak

Task: Strengthen invariants minimally to make them inductive. Prefer semantic patterns (progress, guards, coupling) that block the CE and generalize.
Do not change executable code or requires/ensures.

{COMMON_RULES}

Few-shot mutations:
{examples}

Current proof:
```rust
{proof_content}
```

Inferred verdict rationale:
{verdict_rationale or ''}

Error: {verus_error.error.name} — {verus_error.get_text()}
Console output:
```
{console_error_msg}
```
Counterexamples:
```
{cex_info}
```
Original (reference, DO NOT change code/specs):
```rust
{original_proof}
```
Unified diff (reference for unintended edits):
```
{diff}
```

Output the fixed proof with updated invariants, wrapped in a single Rust block ```rust <code>``` in the end and a brief explanation of what you changed and why.
"""
    return prompt


def create_mutator_prompt_other(
    proof_content: str,
    verus_error: VerusError,
    console_error_msg: str,
    counter_examples: Optional[List[CounterExample]],
    original_proof: str,
    diff: str,
    verdict_rationale: Optional[str] = None,
) -> str:
    examples = """
Example 1 (Add `reveal` to unfold an opaque spec function):
Before: // Fails to prove inductiveness of the `filter` invariant
    while (i < xlen)
        invariant
            y@ == x@.take(i as int).filter(|k:u64| k%3 == 0),
    {
        if (x[i] % 3 == 0) { y.push(x[i]); }
        i = i + 1;
    }
After:
    while (i < xlen)
        invariant
            y@ == x@.take(i as int).filter(|k:u64| k%3 == 0),
    {
        if (x[i] % 3 == 0) { y.push(x[i]); }
        reveal(Seq::filter); // <-- ADDED
        i = i + 1;
    }
Why: The verifier treats `Seq::filter` as an uninterpreted function by default. Adding `reveal(Seq::filter)` exposes its definition, allowing the SMT solver to understand how `y.push` correctly maintains the invariant.

Example 2 (Add a bridging `assert` for sequence induction):
Before: // Fails with InvFailEnd because the relation between states is not obvious
    while index < arr.len()
        invariant
            sum == sum_to(arr@.subrange(start as int, index as int)),
    {
        sum = sum + arr[index] as i128;
        index += 1;
    }
After:
    while index < arr.len()
        invariant
            sum == sum_to(arr@.subrange(start as int, index as int)),
    {
        // ADDED a bridging assertion (lemma)
        assert(arr@.subrange(start as int, index as int) == arr@.subrange(
            start as int, (index + 1) as int).drop_last());
        sum = sum + arr[index] as i128;
        index += 1;
    }
Why: The verifier needs help connecting the sequence `subrange(..., index)` before the update to `subrange(..., index + 1)` after. This `assert` states a trivial but necessary lemma about sequence operations that bridges the inductive step.

Of course, here is the example in plain text format.

Example 3 (Introduce a proof block and helper lemma for a complex property)

Before:
This code fails with an InvFailEnd error. The verifier cannot prove that the uniqueness invariant is maintained after result.push(...).

// Fails to prove the uniqueness invariant is preserved
while index < arr.len()
invariant
// Invariant states that all elements in result so far are unique
forall|m: int, n: int|
0 <= m < n < result.len() ==> #[trigger] result[m] != #[trigger] result[n],
{
if !contains(&result, arr[index]) {
// The verifier gets stuck here. It doesn't know that if result
// is unique and arr[index] isn't in result, then pushing
// arr[index] onto result creates a new, still-unique vector.
result.push(arr[index]);
}
index += 1;
}

After:
The fix is to write a lemma that formalizes the exact logical step the verifier is missing and then apply that lemma in a proof block right before the code that needs it.

// ADDED: A dedicated proof function (lemma) that explains how uniqueness is preserved.
proof fn lemma_push_preserves_uniqueness<T>(seq: Seq<T>, item: T)
requires
// Condition 1: The original sequence is unique
(forall|m: int, n: int| 0 <= m < n < seq.len() ==> #[trigger] seq[m] != #[trigger] seq[n]),
// Condition 2: The new item is not already in the sequence
!seq.contains(item),
ensures
// Result: The new sequence after pushing the item is also unique
(forall|m: int, n: int| 0 <= m < n < seq.push(item).len() ==>
#[trigger] seq.push(item)[m] != #[trigger] seq.push(item)[n]),
{}

// ... inside the function body ...

while index < arr.len()
invariant
forall|m: int, n: int|
0 <= m < n < result.len() ==> #[trigger] result[m] != #[trigger] result[n],
{
if !contains(&result, arr[index]) {
// ADDED: A proof block to apply the lemma, giving the verifier the missing step.
proof {
lemma_push_preserves_uniqueness(result@, arr[index]);
}
result.push(arr[index]);
}
index += 1;
}

Why:
The verifier is not powerful enough to automatically deduce that pushing a new, distinct element onto a unique sequence preserves its uniqueness. This logical step, while obvious to us, must be stated explicitly. The fix involves two parts:

We write a proof fn (a lemma) that formally states this property. It says, "If a sequence is unique and an item is not in it, then the new sequence formed by pushing the item is also unique."

We then call this lemma inside a proof block immediately before the result.push() call. This acts as a direct hint to the verifier, providing it with the exact piece of reasoning it needs to prove that the loop invariant holds for the next iteration.

Example 4 (Add a `trigger` to a `forall` invariant to guide the solver):
Before: // Fails to use the invariant to prove a property, causing an overflow check to fail
    while index < arr.len()
        invariant
            forall|j: int| 0 <= j <= index ==> sum_negative_to(arr@.subrange(0, j)) <= 0,
            sum_negative_to(arr@.subrange(0, index as int)) == sum_neg,
    { ... }
After:
    while index < arr.len()
        invariant
            forall|j: int| 0 <= j <= index ==> sum_negative_to(#[trigger] arr@.subrange(0, j)) <= 0,
            sum_negative_to(arr@.subrange(0, index as int)) == sum_neg,
    { ... }
Why: The verifier didn't know when to apply the `forall` invariant. Adding `#[trigger]` to `arr@.subrange(0, j)` tells the solver to instantiate this rule whenever it sees a term of that shape, which is essential for proving the arithmetic is safe.

Example 5 (Add a hint `assert` to prove a custom spec function's inductive step)

Before:
*This code fails to prove its postcondition. The verifier understands the loop invariant `res == is_prime_so_far(...)` but cannot automatically deduce how the line `res = res && n % k != 0` successfully maintains that invariant for the next iteration (`k+1`).*

// Fails because the inductive step for `is_prime_so_far` is not obvious to the verifier.
while (k < n)
    invariant
        2 <= k <= n,
        res == is_prime_so_far(n as nat, k as nat),
    decreases n - k,
{
    // The verifier doesn't automatically connect this update
    // to the definition of `is_prime_so_far(n, k+1)`.
    res = res && n % k != 0;
    k = k + 1;
}

After:
*The fix is to add an `assert` that explicitly states the relationship between `is_prime_so_far(n, k)` and `is_prime_so_far(n, k+1)`. This gives the verifier the missing logical step.*

// ... inside the function body ...
while (k < n)
    invariant
        2 <= k <= n,
        res == is_prime_so_far(n as nat, k as nat),
    decreases n - k,
{
    // ADDED: An assertion that acts as a lemma for the spec function's inductive step.
    assert((is_prime_so_far(n as nat, k as nat) && (n as nat) % (k as nat) != 0)
        == is_prime_so_far(n as nat, (k + 1) as nat));
    res = res && n % k != 0;
    k = k + 1;
}

Why:
Custom `spec` functions, like `is_prime_so_far`, can be opaque to the verifier. While it knows the function's definition, it doesn't automatically derive complex properties, such as how the function's result for `k` relates to its result for `k+1`.

The added `assert` statement acts as a **lemma** or a **hint**. It explicitly proves the inductive step for the `spec` function, stating that "being prime up to `k+1` is the same as being prime up to `k` and also not being divisible by `k`." By providing this missing logical connection, the `assert` allows the verifier to understand how the code in the loop body correctly maintains the invariant, which is necessary to ultimately prove the function's postcondition.
"""

    cex_info = ""
    if counter_examples is not None:
        try:
            cex_info = json.dumps([cex.to_dict() for cex in counter_examples], indent=2)
        except Exception:
            cex_info = str(counter_examples)

    prompt = f"""
# Mutator: other

Task: Make minimal, semantically meaningful invariant/assertion adjustments to address the failure while preserving behavior and specs.
Do not change executable code or requires/ensures.

{COMMON_RULES}

Few-shot mutations:
{examples}

Current proof:
```rust
{proof_content}
```

Inferred verdict rationale:
{verdict_rationale or ''}

Error: {verus_error.error.name} — {verus_error.get_text()}
Console output:
```
{console_error_msg}
```
Counterexamples:
```
{cex_info}
```
Original (reference, DO NOT change code/specs):
```rust
{original_proof}
```
Unified diff (reference for unintended edits):
```
{diff}
```

Output the fixed proof with updated invariants, wrapped in a single Rust block ```rust <code>``` in the end and a brief explanation of what you changed and why.
"""
    return prompt


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
