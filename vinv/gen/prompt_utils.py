import json
import re
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from vinv.config import PROMPT_ROOT_DIR

PROMPT_ENV = Environment(
    loader=FileSystemLoader(PROMPT_ROOT_DIR),
    undefined=StrictUndefined,
    autoescape=False,
)


def render_prompt(template_name: str, **context: object) -> str:
    if not template_name.endswith(".j2"):
        raise ValueError(f"Prompt templates must use .j2 files: {template_name}")
    return PROMPT_ENV.get_template(template_name).render(**context).strip()


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
