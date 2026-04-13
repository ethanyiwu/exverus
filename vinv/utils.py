import json
import re
import subprocess
from ast import Dict
from pathlib import Path
from typing import Optional


def check_status(status_file: Path, expected_status: str) -> bool:
    """
    Check the status file for the expected status.
    Args:
        status_file (Path): The path to the status file.
        expected_status (str): The expected status to check for.
    Returns:
        bool: True if the status matches, False otherwise.
    """
    if not status_file.is_file():
        raise FileNotFoundError(f"Status file not found: {status_file}")

    with open(status_file, "r") as file:
        content = file.read().strip()

    return content == expected_status


def extract_rs_code_from_response(response: str) -> Optional[str]:
    """Extract the fixed Rust code from the LLM response."""

    # Look for rust code block
    rust_pattern = r"```rust\s*\n(.*?)\n```"
    rust_match = re.search(rust_pattern, response, re.DOTALL)

    if rust_match:
        return rust_match.group(1).strip()

    # Fallback: look for any code block
    code_pattern = r"```\s*\n(.*?)\n```"
    code_match = re.search(code_pattern, response, re.DOTALL)

    if code_match:
        code = code_match.group(1).strip()
        # Check if it looks like Rust code
        if any(
            keyword in code
            for keyword in ["fn ", "let ", "struct ", "impl ", "use ", "proof "]
        ):
            return code

    return None


def extract_python_code_block(text: str) -> Optional[str]:
    """Extract a ```python ... ``` code block if present, otherwise a generic fenced block.

    Returns the inner code content without fences, or None if not found.
    """
    m = re.search(r"```(?:python)?\n([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def diff(file1: Path, file2: Path, output_file: Path) -> None:
    """
    Compare two files and write the differences to an output file.
    Args:
        file1 (Path): The first file to compare.
        file2 (Path): The second file to compare.
        output_file (Path): The file to write the differences to.
    """
    with open(output_file, "w") as out_file:
        subprocess.run(
            ["diff", "-uw", file1.as_posix(), file2.as_posix()],
            stdout=out_file,
            stderr=subprocess.DEVNULL,
            text=True,
        )


def program_with_line_no(file: Path) -> str:
    """
    Read a file and return its content with line numbers.
    Args:
        file (Path): The file to read.
    Returns:
        str: The content of the file with line numbers.
    """
    if not file.is_file():
        raise FileNotFoundError(f"File not found: {file}")

    with open(file, "r") as f:
        lines = f.readlines()

    return "".join(f"{i + 1}: {line}" for i, line in enumerate(lines))

def get_last_attempt_file(attempt_dir: Path, attempt_file_name: str) -> Path:
    """
    Get the last attempt file in the attempt directory.
    """

    last_try_dir = max(
        attempt_dir.glob("try_*"), key=lambda f: int(f.stem.split("_")[-1])
    )
    last_attempt_file = last_try_dir / attempt_file_name
    assert (
        last_attempt_file.is_file()
    ), f"Last attempt file not found: {last_attempt_file}"

    return last_attempt_file


def json_load(file: Path) -> Dict:
    """
    Load a JSON file.
    """
    with open(file, "r") as f:
        return json.load(f)
