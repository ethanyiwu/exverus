import json
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Tuple

from loguru import logger
from veval import VerusError, VerusErrorType, VEval

from vinv.gen.client import request_prompt_one
from vinv.gen.prompt_utils import make_unified_diff, render_prompt
from vinv.pipeline.cex_validation_backend import (
    CexValidationBackend,
    prepare_extracted_harness,
    validate_cex_list_with_backend,
)
from vinv.pipeline.counter_example import CounterExample, add_validate_status
from vinv.pipeline.error_priority import sort_errors_by_priority
from vinv.pipeline.mut_val_generalization import mut_val_cex_generalization
from vinv.pipeline.parser_utils import error_inside_loop
from vinv.pipeline.simple_cex import simple_cex_generation
from vinv.pipeline.simple_generalization import simple_cex_generalization
from vinv.pipeline.trajectory import recorder
from vinv.pipeline.verification_cex import verification_cex_generation
from vinv.pipeline.z3_cex import z3_cex_generation
from vinv.pipeline.z3_generalization import z3_cex_generalization
from vinv.utils import check_status, extract_rs_code_from_response
from vinv.verus_utils import record_verify_status, verify_with_verus


def extract_and_prioritize_errors(proof_file: Path) -> List[VerusError]:
    """Run VEval on the proof to extract Verus errors and sort by priority."""
    code = proof_file.read_text()
    veval = VEval(code, logger)
    veval.eval_and_get_score()
    errors = veval.get_failures()  # List[VerusError]
    return sort_errors_by_priority(errors)


def cex_compilation_repair(
    buggy_proof_file: Path,
    console_error_msg: str,
    try_dir: Path,
    model: str = "gpt-4o",
    original_proof_file: Path | None = None,
) -> Path:
    """Fix compilation errors using a dedicated prompt.

    Args:
        buggy_proof_file: path to the current (buggy) proof to repair
        original_proof_file: path to the original unverified proof to
            be used as canonical reference for diffs and cross-checks
    """
    try_dir.mkdir(parents=True, exist_ok=True)

    buggy_proof_content = buggy_proof_file.read_text()

    assert (
        original_proof_file is not None
    ), "original_proof_file is required for compilation repair"
    original = original_proof_file.read_text()
    prompt = render_prompt(
        "iterative/compilation_repair.j2",
        proof_content=buggy_proof_content,
        original_proof=original,
        diff=make_unified_diff(original, buggy_proof_content),
        error_message=console_error_msg,
    )

    system_prompt = render_prompt("pipeline/cex/compilation_repair_system.j2")
    response = request_prompt_one(
        prompt,
        system=system_prompt,
        model=model,
        max_retry=5,
        temperature=1.0,
        task_id=str(try_dir),
        prompt_type_id="compilation_repair",
    )

    (try_dir / "conversation.json").write_text(
        json.dumps(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ],
            indent=2,
        )
    )
    (try_dir / "response.txt").write_text(response)

    fixed_proof_code = extract_rs_code_from_response(response)
    fixed_proof_path = try_dir / "repaired.rs"
    fixed_proof_path.write_text(fixed_proof_code)
    return fixed_proof_path


# --- Strategy registry (plug-in) -------------------------------------------------

# Signatures for strategies
CexGenerationFunc = Callable[
    [Path, Optional[Path], VerusError, Path, str, str, int, CexValidationBackend],
    Optional[List[CounterExample]],
]
CexGeneralizationFunc = Callable[
    [
        Path,
        VerusError,
        Optional[List[CounterExample]],
        Path,
        str,
        Path,
        str,
        str,
        CexValidationBackend,
    ],
    Optional[Path],
]

# Default registries (name -> callable)
_CEX_GENERATION_STRATEGIES: Dict[str, CexGenerationFunc] = {
    "simple": simple_cex_generation,
    "z3": z3_cex_generation,
    "verification": verification_cex_generation,
}

_CEX_GENERALIZATION_STRATEGIES: Dict[str, CexGeneralizationFunc] = {
    "simple": simple_cex_generalization,
    "z3": z3_cex_generalization,
    "mut_val": mut_val_cex_generalization,
}


def register_cex_generation_strategy(name: str, fn: CexGenerationFunc) -> None:
    """Register a counterexample generation strategy plug-in."""
    _CEX_GENERATION_STRATEGIES[name] = fn


def register_cex_generalization_strategy(name: str, fn: CexGeneralizationFunc) -> None:
    """Register a counterexample generalization strategy plug-in."""
    _CEX_GENERALIZATION_STRATEGIES[name] = fn


def is_cex_generatable(error: VerusError) -> bool:
    """Classify whether we should attempt semantic counterexample generation for this error.

    Conservative: treat PostCondFail, decreases failures, and structural/mode/type issues as non-CE.
    """
    et = error.error
    non_cex_types = {
        VerusErrorType.MismatchedType,
        VerusErrorType.ExecinGhost,
        VerusErrorType.RustAssert,
        VerusErrorType.UnxProofBlock,
        VerusErrorType.RecommendNotMet,
        VerusErrorType.DecFailEnd,
        VerusErrorType.DecFailCont,
        VerusErrorType.Other,
    }
    return et not in non_cex_types


def generate_and_generalize(
    current_proof_file: Path,
    verus_error: VerusError,
    try_dir: Path,
    console_error_msg: str,
    original_proof_file: Path,
    diff: str,
    model: str,
    cex_generation_strategy: Literal["z3", "simple", "verification"],
    cex_generalization_strategy: Literal["z3", "simple", "mut_val"],
    num_cex: int,
    enable_validation: bool = True,
    cex_validation_backend: CexValidationBackend = "v2",
) -> Tuple[Optional[Path], Optional[List[CounterExample]]]:
    """Run CEX generation and generalization as a single pipeline step.

    Returns a tuple of (fixed_proof_path, counter_examples).
    """
    # Optionally perform loop harness extraction and CEX validation
    # prepare extracted file for CEX generation
    if enable_validation and error_inside_loop(current_proof_file, verus_error):
        harness_before_dir = try_dir / "harness_before"
        harness_before_dir.mkdir(parents=True, exist_ok=True)
        before_extracted_file = harness_before_dir / "extracted_loop.rs"
        prepare_extracted_harness(
            current_proof_file,
            verus_error,
            before_extracted_file,
            backend=cex_validation_backend,
        )
    else:
        before_extracted_file = None
    # CEX generation
    gen_fn = _CEX_GENERATION_STRATEGIES.get(cex_generation_strategy)
    if gen_fn is None:
        raise ValueError(f"Unknown cex generation strategy: {cex_generation_strategy}")
    counter_examples = gen_fn(
        current_proof_file,
        before_extracted_file,
        verus_error,
        try_dir,
        console_error_msg,
        model,
        num_cex,
        cex_validation_backend,
    )

    # Optionally perform loop harness extraction and CEX validation
    if enable_validation and error_inside_loop(current_proof_file, verus_error):
        if counter_examples:
            baseline_results = validate_cex_list_with_backend(
                extracted_file=before_extracted_file,
                counter_examples=counter_examples,
                validation_dir=harness_before_dir,
                backend=cex_validation_backend,
            )
            # Record per-CE validation status and filter to true CEXs
            add_validate_status(
                counter_examples=counter_examples,
                results=baseline_results,
                key=str(before_extracted_file),
                target_error=verus_error,
            )
            validated_counter_examples = [
                ce
                for ce in counter_examples
                if ce.validate_status.get(str(before_extracted_file)).get("true_cex")
            ]
            logger.info(f"Validated {len(validated_counter_examples)} CEXs")
            logger.info(
                f"Validated CEXs: {[ce.cex_index for ce in validated_counter_examples]}"
            )
            logger.info(
                f"filtered out {len(counter_examples) - len(validated_counter_examples)} CEXs"
            )
        else:
            # no cexs to validate
            validated_counter_examples = []
            logger.info("No CEXs to validate")

    # CEX generalization
    genz_fn = _CEX_GENERALIZATION_STRATEGIES.get(cex_generalization_strategy)
    if genz_fn is None:
        raise ValueError(
            f"Unknown cex generalization strategy: {cex_generalization_strategy}"
        )

    fixed_proof_path = genz_fn(
        current_proof_file,
        verus_error,
        validated_counter_examples if enable_validation else counter_examples,
        try_dir,
        console_error_msg,
        original_proof_file,
        diff,
        model,
        cex_validation_backend,
    )

    return fixed_proof_path, counter_examples


def cex_iterative_repair(
    error_proof_file: Path,
    console_error_msg: str,
    cex_repair_dir: Path,
    original_proof_file: Path,
    model: str = "gpt-4o",
    max_try: int = 5,
    cex_generation_strategy: Literal["z3", "simple", "verification"] = "simple",
    cex_generalization_strategy: Literal["z3", "simple", "mut_val"] = "simple",
    num_cex: int = 10,
    cex_validation_backend: CexValidationBackend = "v2",
) -> Path:
    """Iteratively repair using IC3-guided counterexamples and generalization."""
    cex_repair_dir.mkdir(parents=True, exist_ok=True)
    current_proof_file = error_proof_file

    # Enable trajectory recording only for the requested combination at run level
    record_traj = (
        cex_generation_strategy == "z3" and cex_generalization_strategy == "mut_val"
    )
    recorder.enable(record_traj)
    if record_traj:
        recorder.init_run(
            cex_repair_dir,
            cex_generation_strategy,
            cex_generalization_strategy,
            num_cex,
        )

    for attempt in range(1, max_try + 1):
        try_dir = cex_repair_dir / f"try_{attempt}"
        try_dir.mkdir(parents=True, exist_ok=True)

        # Separate files for the input (pre-repair) verifier run and the
        # repaired (post-repair) verifier run so outputs don't overwrite each
        # other and we can preserve both traces for debugging.
        input_stdout_file = try_dir / "input_out.txt"
        input_stderr_file = try_dir / "input_err.txt"
        repaired_stdout_file = try_dir / "repaired_out.txt"
        repaired_stderr_file = try_dir / "repaired_err.txt"
        repair_status_json = try_dir / "repair_status.json"
        repair_status_txt = try_dir / "repair_status.txt"
        repair_diff_file = try_dir / "diff_before_after.diff"

        # Run verifier on the current proof and record its status using helpers
        verification_passed = verify_with_verus(
            proof_file=current_proof_file,
            stdout_file=input_stdout_file,
            stderr_file=input_stderr_file,
        )
        input_status_file = try_dir / "input_verify_status.txt"
        verification_passed_2 = record_verify_status(
            current_proof_file, input_status_file, override=True
        )
        assert (
            verification_passed == verification_passed_2
        ), f"Verification status mismatch for {current_proof_file}"

        console_error_msg = (
            f"{input_stderr_file.read_text()}\n{input_stdout_file.read_text()}"
        )
        has_compilation_error = check_status(input_status_file, "compilation_error")

        # Compilation-repair branch
        if has_compilation_error:
            if record_traj:
                # Record iteration header for compilation error attempt
                recorder.begin_iteration(
                    attempt,
                    "compilation_error",
                    [],
                )
            fixed_proof_path = cex_compilation_repair(
                buggy_proof_file=current_proof_file,
                console_error_msg=console_error_msg,
                try_dir=try_dir,
                model=model,
                original_proof_file=original_proof_file,
            )

            if not (fixed_proof_path and fixed_proof_path.exists()):
                raise ValueError(
                    f"Failed to produce repaired file for compilation error on attempt {attempt}"
                )

            make_unified_diff(
                current_proof_file.read_text(),
                fixed_proof_path.read_text(),
                out_path=repair_diff_file,
            )

            # Verify repaired file and record status
            verification_passed_fixed = verify_with_verus(
                proof_file=fixed_proof_path,
                stdout_file=repaired_stdout_file,
                stderr_file=repaired_stderr_file,
            )
            repaired_status_file = try_dir / "repaired_verify_status.txt"
            repaired_verified = record_verify_status(
                fixed_proof_path, repaired_status_file, override=True
            )
            if not verification_passed_fixed == repaired_verified:
                logger.warning(f"Verification status mismatch for {fixed_proof_path}")
                verification_passed_fixed = (
                    repaired_verified and verification_passed_fixed
                )

            status = {
                "attempt": attempt,
                "attempt_type": "compilation",
                "error_type": "compilation_error",
                "counter_example": None,
                "fixed_proof_path": str(fixed_proof_path),
                "verification_passed": verification_passed_fixed,
                "has_compilation_error": check_status(
                    repaired_status_file, "compilation_error"
                ),
            }
            repair_status_json.write_text(json.dumps(status, indent=2))
            if verification_passed_fixed:
                repair_status_txt.write_text("verification_pass")
                logger.info(
                    f"Verification passed for {fixed_proof_path} on attempt {attempt}"
                )
                if record_traj:
                    recorder.record_status(
                        attempt,
                        verification_passed=True,
                        compilation_error=check_status(
                            repaired_status_file, "compilation_error"
                        ),
                    )
                return fixed_proof_path
            elif check_status(repaired_status_file, "compilation_error"):
                repair_status_txt.write_text("compilation_error")
                if record_traj:
                    recorder.record_status(
                        attempt,
                        verification_passed=False,
                        compilation_error=True,
                    )
            else:
                repair_status_txt.write_text("verification_error")
                if record_traj:
                    recorder.record_status(
                        attempt,
                        verification_passed=False,
                        compilation_error=False,
                    )

            current_proof_file = fixed_proof_path
            continue

        errors = extract_and_prioritize_errors(current_proof_file)
        if not errors:
            logger.info(f"All errors fixed after {attempt} attempts")
            return current_proof_file

        logger.info(f"Attempt {attempt}/{max_try}")
        logger.info(
            f"Found {len(errors)} errors, targeting highest priority error: {errors[0].error}"
        )

        diff = make_unified_diff(
            original_proof_file.read_text(), current_proof_file.read_text()
        )

        # error type based routing (whether CE is meaningful)
        if is_cex_generatable(errors[0]):
            eff_gen_strategy = cex_generation_strategy
            eff_genz_strategy = cex_generalization_strategy
        else:
            eff_gen_strategy = "simple"
            eff_genz_strategy = "simple"
            logger.warning(
                f"falling back to simple strategy for {errors[0].error} due to non-CEX-generatable error type"
            )

        # Disable validation if the error type is not CEX-generatable or the error is not inside a loop
        # or the strategies are simple
        enable_validation_flag = (
            is_cex_generatable(errors[0])
            and error_inside_loop(current_proof_file, errors[0])
            and eff_gen_strategy != "simple"
            and eff_genz_strategy != "simple"
        )

        # Begin iteration trajectory record: always create header for this attempt
        # when the run is configured for z3 + mut_val; record detailed metrics only
        # when the effective strategies match the combo.
        record_this_iter = record_traj and (
            eff_gen_strategy == "z3" and eff_genz_strategy == "mut_val"
        )
        if record_traj:
            recorder.begin_iteration(
                attempt,
                errors[0].error.name if errors else None,
                [e.error.name for e in errors],
            )

        fixed_proof_path, counter_examples = generate_and_generalize(
            current_proof_file=current_proof_file,
            verus_error=errors[0],
            try_dir=try_dir,
            console_error_msg=console_error_msg,
            original_proof_file=original_proof_file,
            diff=diff,
            model=model,
            cex_generation_strategy=eff_gen_strategy,
            cex_generalization_strategy=eff_genz_strategy,
            num_cex=num_cex,
            enable_validation=enable_validation_flag,
            cex_validation_backend=cex_validation_backend,
        )

        # Record CEX stats for this iteration if applicable
        if record_this_iter:
            num_cex_generated = len(counter_examples) if counter_examples else 0
            num_cex_validated = 0
            if enable_validation_flag and counter_examples:
                try:
                    key = str((try_dir / "harness_before" / "extracted_loop.rs"))
                    num_cex_validated = sum(
                        1
                        for ce in counter_examples
                        if ce.validate_status.get(key, {}).get("true_cex")
                    )
                except Exception:
                    num_cex_validated = 0
            recorder.record_cex(attempt, num_cex_generated, num_cex_validated)

        if not (fixed_proof_path and fixed_proof_path.exists()):
            raise ValueError(f"Failed to generate fixed proof in attempt {attempt}")

        make_unified_diff(
            current_proof_file.read_text(),
            fixed_proof_path.read_text(),
            out_path=repair_diff_file,
        )

        verification_passed_fixed = verify_with_verus(
            proof_file=fixed_proof_path,
            stdout_file=repaired_stdout_file,
            stderr_file=repaired_stderr_file,
        )
        repaired_status_file = try_dir / "repaired_verify_status.txt"
        repaired_verified = record_verify_status(
            fixed_proof_path, repaired_status_file, override=True
        )
        if not verification_passed_fixed == repaired_verified:
            logger.warning(f"Verification status mismatch for {fixed_proof_path}")
            verification_passed_fixed = repaired_verified and verification_passed_fixed

        if verification_passed_fixed:
            status = {
                "attempt": attempt,
                "attempt_type": "ic3",
                "error_type": errors[0].error.name if errors else "verification_error",
                "counter_examples": [c.to_dict() for c in counter_examples]
                if counter_examples
                else None,
                "fixed_proof_path": str(fixed_proof_path),
                "verification_passed": True,
                "has_compilation_error": check_status(
                    repaired_status_file, "compilation_error"
                ),
            }
            repair_status_json.write_text(json.dumps(status, indent=2))
            repair_status_txt.write_text("verification_pass")
            logger.info(
                f"Verification passed for {fixed_proof_path} on attempt {attempt}"
            )
            if record_traj:
                recorder.record_status(
                    attempt,
                    verification_passed=True,
                    compilation_error=check_status(
                        repaired_status_file, "compilation_error"
                    ),
                )
            return fixed_proof_path

        status = {
            "attempt": attempt,
            "attempt_type": "ic3",
            "error_type": errors[0].error.name if errors else "verification_error",
            "counter_examples": [c.to_dict() for c in counter_examples]
            if counter_examples
            else None,
            "fixed_proof_path": str(fixed_proof_path),
            "verification_passed": False,
            "has_compilation_error": check_status(
                repaired_status_file, "compilation_error"
            ),
        }
        repair_status_json.write_text(json.dumps(status, indent=2))
        repair_status_txt.write_text("verification_error")

        if record_traj:
            recorder.record_status(
                attempt,
                verification_passed=False,
                compilation_error=check_status(
                    repaired_status_file, "compilation_error"
                ),
            )

        current_proof_file = fixed_proof_path

    logger.warning(f"Failed to fix all errors after {max_try} attempts")
    return current_proof_file
