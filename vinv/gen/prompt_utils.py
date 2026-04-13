import json
import re
import subprocess
import tempfile
from pathlib import Path

from vinv.config import (
    COMPILATION_REPAIR_PROMPT_FILE,
    NAIVE_REPAIR_PROMPT_FILE,
)

VERUS_SYSTEM_PROMPT = "You are an experienced Rust programmer. You are very familiar with Verus, which is a tool for verifying the correctness of code written in Rust."


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
