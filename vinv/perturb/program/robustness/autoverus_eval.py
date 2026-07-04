import subprocess
from fire import Fire
from loguru import logger

from vinv.config import ROOT_DIR
from vinv.data.cherrypick import get_all_obfs_proofs
from vinv.proof_utils import display_proof_status
from vinv.utils import diff
from vinv.verus_utils import record_verify_status

AUTOVERUS_TOOL_DIR = ROOT_DIR / "verus-proof-synthesis" / "code"
# use gpt-4o for now since autoverus used that
# CONFIG_FILE = AUTOVERUS_TOOL_DIR / "config_gpt-4o.json"
CONFIG_FILE = AUTOVERUS_TOOL_DIR / "config_deepseek.json"
assert CONFIG_FILE.is_file(), f"Config file not found: {CONFIG_FILE}"


def main(
    obfuscate_prompt_type: str = "plain",
    model: str = "gpt-4o",
):
    obfs_proofs = get_all_obfs_proofs(
        prompt_type=obfuscate_prompt_type,
        model=model,
        use_specified_taskids=True,
    )

    proof_status = {
        "compilation_error": [],
        "verification_error": [],
        "verification_pass": [],
    }

    for obfs_proof in obfs_proofs:
        response_dir = obfs_proof.path.parent
        deghosted_unverified_file = response_dir / "deghosted_unverified.rs"
        # run autoverus
        autoverus_result_dir = response_dir / "autoverus_result"
        autoverus_result_dir.mkdir(parents=True, exist_ok=True)
        autoverus_output_file = autoverus_result_dir / "autoverus_output.rs"
        autoverus_status_file = autoverus_result_dir / "autoverus_status.txt"
        stdout_file = autoverus_result_dir / "autoverus_stdout.txt"
        stderr_file = autoverus_result_dir / "autoverus_stderr.txt"
        cmd = [
            "python",
            "main.py",
            "--input",
            str(deghosted_unverified_file),
            "--output",
            str(autoverus_output_file),
            "--config",
            str(CONFIG_FILE),
        ]

        if not autoverus_status_file.is_file():
            subprocess.run(
                cmd,
                cwd=AUTOVERUS_TOOL_DIR,
                stdout=open(stdout_file, "w"),
                stderr=open(stderr_file, "w"),
            )

        if not autoverus_status_file.exists():
            # uses `which verus`
            record_verify_status(
                autoverus_output_file,
                autoverus_status_file,
            )

            proof_diff = autoverus_result_dir / "autoverus_vs_gt.diff"
            diff(
                autoverus_output_file.as_posix(),
                obfs_proof.path.as_posix(),
                proof_diff,
            )
        else:
            logger.info(
                f"Skipping verification for {obfs_proof.path} as it has already been processed."
            )

        proof_status[autoverus_status_file.read_text().strip()].append(obfs_proof)

        # Print the results
        display_proof_status(proof_status)


if __name__ == "__main__":
    Fire(main)
