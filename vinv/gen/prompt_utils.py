import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from vinv.config import (
    COMPILATION_REPAIR_PROMPT_FILE,
    INV_GEN_PLAIN_PROMPT_FILE,
    NAIVE_REPAIR_PROMPT_FILE,
    TEST_DRIVER_GEN_HARDCODED_PROMPT_FILE,
    TEST_DRIVER_GEN_STDIN_PROMPT_FILE,
)

VERUS_SYSTEM_PROMPT = "You are an experienced Rust programmer. You are very familiar with Verus, which is a tool for verifying the correctness of code written in Rust."

TEST_TRACE_INFO_PROMPT = """
To help you understand the semantics of the program to be verified and identify incorrect or missing invariants, here is an instrumented program that inserts a few test invocations (in `main`) and logging statements that can print the runtime values of variables to facilitate reasoning of invariants.

instrumented program:

<test_driver_code>

Here is the execution output of the instrumented program. You must explicitly reason based on the execution output, what is not changed between loop interations (likely invariants), whether execution output falsify the existing invariants, etc.:

<execution_output>
"""


def read_inv_gen_prompt(prompt_type: Literal["plain"] = "plain") -> str:
    return _read_prompt({"plain": INV_GEN_PLAIN_PROMPT_FILE}, prompt_type)


def read_test_driver_gen_prompt(
    test_driver_mode: Literal["hardcoded", "stdin"] = "hardcoded",
) -> str:
    return _read_prompt(
        {
            "hardcoded": TEST_DRIVER_GEN_HARDCODED_PROMPT_FILE,
            "stdin": TEST_DRIVER_GEN_STDIN_PROMPT_FILE,
        },
        test_driver_mode,
    )


def read_naive_repair_prompt() -> str:
    return NAIVE_REPAIR_PROMPT_FILE.read_text(encoding="utf-8").strip()


def read_compilation_repair_prompt() -> str:
    return COMPILATION_REPAIR_PROMPT_FILE.read_text(encoding="utf-8").strip()


def read_conversation_file(conversation_file: Path) -> list[dict]:
    return json.loads(conversation_file.read_text(encoding="utf-8"))


def make_unified_diff(
    original: str,
    modified: str,
    out_path: Path | None = None,
) -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_path = Path(tmp_dir) / "original.txt"
        modified_path = Path(tmp_dir) / "modified.txt"
        original_path.write_text(original, encoding="utf-8")
        modified_path.write_text(modified, encoding="utf-8")
        diff_out = subprocess.run(
            ["diff", "-uw", str(original_path), str(modified_path)],
            capture_output=True,
            text=True,
        ).stdout
    if out_path is not None:
        out_path.write_text(diff_out, encoding="utf-8")
    return diff_out


def write_conversation_file(
    conversations: list[dict],
    conversation_file: Path,
) -> None:
    conversation_file.write_text(
        json.dumps(conversations, indent=4),
        encoding="utf-8",
    )


def count_tokens(
    content: str,
    model: str = "gpt-4o",
) -> int:
    if model.startswith(("gpt-", "o1", "o3", "o4", "deepseek")):
        return len(re.findall(r"[A-Za-z_]+|[0-9]+|\n|[^\w\s]", content))
    raise ValueError(f"Unknown model: {model}.")


def _read_prompt(prompt_files: dict[str, Path], prompt_type: str) -> str:
    prompt_file = prompt_files.get(prompt_type)
    if prompt_file is None:
        supported = ", ".join(sorted(prompt_files))
        raise ValueError(
            f"Unknown template: {prompt_type}. Supported templates: {supported}."
        )
    return prompt_file.read_text(encoding="utf-8").strip()
