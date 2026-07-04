import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from loguru import logger
from veval import EvalScore, VerusError, VEval  # type: ignore

from vinv.config import resolve_verus_path
from vinv.pipeline.error_priority import sort_errors_by_priority
from vinv.utils import check_status


def extract_and_prioritize_errors_from_log(log_file: Path) -> list[VerusError]:
    """
    Similar to `vinv.pipeline.cex.extract_and_prioritize_errors`, but extracts error types
    from an existing Verus log file (e.g., `repaired_err.txt`) instead of running VEval.

    This follows the parsing approach used in `verus-proof-synthesis/code/veval.py`:
    - The log is expected to contain JSON lines (e.g., rustc/verus `--error-format=json` output).
      We parse each line as JSON and construct `VerusError(e)` for each `"level":"error"`.

    Returns:
        A list of `veval.VerusError`, sorted by the same priority used in
        `vinv.pipeline.error_priority`.
    """
    if not log_file.is_file():
        return []

    text = log_file.read_text(errors="replace")

    errors: list[VerusError] = []

    # JSON-per-line (matches VEval parsing logic)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(e, dict):
            continue
        if e.get("level") != "error":
            continue
        msg = e.get("message")
        if isinstance(msg, str) and "aborting due to" in msg:
            continue
        try:
            errors.append(VerusError(e))
        except Exception:
            # If the dict schema isn't what VerusError expects, skip it.
            continue

    return sort_errors_by_priority(errors)


def verify_with_verus(
    proof_file: Path,
    stdout_file: Path | None = None,
    stderr_file: Path | None = None,
    use_old_verus: bool = False,
    max_errs: int = 5,
) -> bool:
    """
    Verify the proof file with Verus.
    """
    cmd = [resolve_verus_path(use_old_verus), str(proof_file)]
    cmd += ["--multiple-errors", str(max_errs)]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if stdout_file is not None:
        stdout_file.parent.mkdir(parents=True, exist_ok=True)
        stdout_file.write_text(result.stdout)
    if stderr_file is not None:
        stderr_file.parent.mkdir(parents=True, exist_ok=True)
        stderr_file.write_text(result.stderr)

        if stdout_file is None:
            # append stdout content to stderr if stdout_file is not provided
            stderr_file.write_text(result.stdout + "\n" + result.stderr)

    if result.returncode != 0:
        return False
    else:
        return True


def get_verus_result(
    proof_file: Path, use_old_verus: bool = False
) -> tuple[bool, str, str]:
    """
    Run Verus on the file.
    Returns a tuple of (success, stdout, stderr).
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        stdout_file = Path(temp_dir) / "stdout.txt"
        stderr_file = Path(temp_dir) / "stderr.txt"
        success = verify_with_verus(
            proof_file,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
            use_old_verus=use_old_verus,
        )
        stdout = stdout_file.read_text() if stdout_file.exists() else ""
        stderr = stderr_file.read_text() if stderr_file.exists() else ""

    return success, stdout, stderr


def verus_format(proof_file: Path) -> bool:
    """
    Format the Verus proof file using the Verus formatter.
    """
    verus_formatter_bin = shutil.which("verusfmt")
    if verus_formatter_bin is None:
        logger.error(
            "Verus formatter not found. Please ensure 'verusfmt' is installed."
        )
        return False
    cmd = [verus_formatter_bin, str(proof_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Formatting failed for {proof_file}: {result.stderr}")
        return False
    else:
        return True


def record_verify_status(
    proof_file: Path,
    verify_status_file: Path,
    override: bool = False,
) -> bool:
    """
    Record the verification status of the proof file.
    Returns True if verification is successful, False otherwise.
    If the verification status file already exists, it will be overwritten (if
    override is True). Otherwise, the verification status will be read from the
    file.
    """
    if not verify_status_file.exists() or override:
        veval = VEval(proof_file.read_text(), logger)
        score = veval.eval_and_get_score()
        if score.compilation_error:
            verify_status_file.write_text("compilation_error")
        elif score.errors > 0:
            verify_status_file.write_text("verification_error")
        else:
            verify_status_file.write_text("verification_pass")
    else:
        logger.info(
            f"Skipping verification for {proof_file} as it has already been processed."
        )

    return check_status(verify_status_file, "verification_pass")


def record_verify_status_for_proof_folder(
    proof_folder: Path,
    verify_status_file: Path,
) -> bool:
    """
    Record the verification status for all proof files in a folder.
    Returns True if any proof is successfully verified, False otherwise.
    """
    any_verified = False
    verify_result = (
        {}
    )  # {proof_file: {'status': status, 'verus_out': verus_out, 'rustc_out': rustc_out}}

    if verify_status_file.is_file() and verify_status_file.stat().st_size > 0:
        verify_result = json.loads(verify_status_file.read_text())
        return any(
            verify_result[proof_name]["status"] == "verification_pass"
            for proof_name in verify_result
        )

    for proof_file in proof_folder.glob("*.rs"):
        veval = VEval(proof_file.read_text(), logger)
        veval.eval_and_get_score()
        errors = veval.get_failures()
        verify_status = (
            "compilation_error"
            if veval.compilation_error
            else "verification_error"
            if errors
            else "verification_pass"
        )
        verify_result[proof_file.name] = {
            "status": verify_status,
            "verus_out": veval.verus_out,
            "rustc_out": veval.rustc_out,
        }
        if verify_status == "verification_pass":
            any_verified = True

    verify_status_file.write_text(json.dumps(verify_result, indent=2))

    return any_verified


def get_console_error_msg_from_rustc_out(rustc_out: str) -> str:
    """
    Extract the console error message from rustc output.
    """
    console_error_message_list = []
    for rust_err in rustc_out.split("\n")[:-1]:
        try:
            e = json.loads(rust_err)
        except json.JSONDecodeError:
            continue
        console_error_message_list.append(e["rendered"])

    return "\n".join(console_error_message_list)


def get_verus_errors_score(proof_file: Path) -> tuple[list[VerusError], EvalScore]:
    """
    Get the verus errors from the proof file.
    """
    veval = VEval(proof_file.read_text(), logger)
    score = veval.eval_and_get_score()
    assert (
        not score.compilation_error
    ), f"Proof {proof_file} has compilation error: {score.compilation_error}"
    assert score.errors > 0, f"Proof {proof_file} has no errors: {score.errors}"

    return veval.get_failures(), score
