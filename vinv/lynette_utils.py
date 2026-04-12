import os
import subprocess
from pathlib import Path

from loguru import logger


def code_change_is_safe(
    ori_file: Path,
    new_file: Path,
) -> bool:
    """
    This function is a shorter version of verus-proof-synthesis's code/utils.py
    `code_change_is_safe` function.
    """
    LYNETTE_PATH = os.environ.get("LYNETTE_PATH")
    if LYNETTE_PATH is None:
        raise ValueError("LYNETTE_PATH environment variable is not set.")
    cmd = [
        LYNETTE_PATH,
        "compare",
        str(ori_file),
        str(new_file),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # unsafe code change
        logger.info(
            f"Unsafe code change detected between {ori_file} and {new_file}:\n{result.stdout}\n{result.stderr}"
        )
        return False
    else:
        # safe code change
        logger.info(
            f"Safe code change detected between {ori_file} and {new_file}."
        )
        return True
