import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Literal

import tiktoken

from vinv.config import (
    COMPILATION_REPAIR_PROMPT_FILE,
    INV_GEN_PLAIN_PROMPT_FILE,
    NAIVE_REPAIR_PROMPT_FILE,
    OBFUSC_PROMPT_FILE,
    REPAIR_WITH_TRACE_PROMPT_FILE,
    SOLUTION_GEN_PROMPT_FILE,
    TEST_DRIVER_GEN_CEX_PROMPT_FILE,
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
    """
    Read the invariant generation prompt from a file.
    Args:
        template (Literal["plain"]): The template to use for the prompt.
    Returns:
        str: The invariant generation prompt.
    """
    if prompt_type == "plain":
        prompt_file = INV_GEN_PLAIN_PROMPT_FILE
    else:
        raise ValueError(
            f"Unknown template: {prompt_type}. Supported templates: plain."
        )
    with open(prompt_file, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_obfuscation_prompt(prompt_type: Literal["plain"] = "plain") -> str:
    """
    Read the obfuscation prompt from a file.
    Args:
        prompt_type (Literal["plain"]): The type of prompt to read.
    Returns:
        str: The obfuscation prompt.
    """
    if prompt_type == "plain":
        prompt_file = OBFUSC_PROMPT_FILE
    else:
        raise ValueError(
            f"Unknown template: {prompt_type}. Supported templates: plain."
        )

    with open(prompt_file, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_solution_gen_prompt(
    prompt_type: Literal["rust_solution_gen"] = "rust_solution_gen",
) -> str:
    """
    Read the solution generation prompt from a file.
    Args:
        prompt_type (Literal["rust_solution_gen"]): The type of prompt to read.
    Returns:
        str: The solution generation prompt.
    """
    if prompt_type == "rust_solution_gen":
        prompt_file = SOLUTION_GEN_PROMPT_FILE
    else:
        raise ValueError(
            f"Unknown template: {prompt_type}. Supported templates: rust_solution_gen."
        )

    with open(prompt_file, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_test_driver_gen_prompt(
    test_driver_mode: Literal["hardcoded", "stdin", "context"] = "hardcoded",
) -> str:
    """
    Read the test driver generation prompt from a file.
    Args:
        test_driver_mode (Literal["hardcoded", "stdin", "context"]): The type of prompt to read.
    Returns:
        str: The test driver generation prompt.
    """
    if test_driver_mode == "hardcoded":
        prompt_file = TEST_DRIVER_GEN_HARDCODED_PROMPT_FILE
    elif test_driver_mode == "stdin":
        prompt_file = TEST_DRIVER_GEN_STDIN_PROMPT_FILE
    elif test_driver_mode == "cex":
        prompt_file = TEST_DRIVER_GEN_CEX_PROMPT_FILE
    else:
        raise ValueError(
            f"Unknown template: {test_driver_mode}. Supported templates: hardcoded, stdin, context."
        )

    with open(prompt_file, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_repair_with_trace_prompt(
    prompt_type: Literal["plain"] = "plain",
) -> str:
    """
    Read the repair with trace prompt from a file.
    """
    if prompt_type == "plain":
        prompt_file = REPAIR_WITH_TRACE_PROMPT_FILE
    else:
        raise ValueError(
            f"Unknown template: {prompt_type}. Supported templates: plain."
        )

    with open(prompt_file, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_naive_repair_prompt() -> str:
    """
    Read the naive repair prompt from a file.
    """

    with open(NAIVE_REPAIR_PROMPT_FILE, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_compilation_repair_prompt() -> str:
    """
    Read the compilation repair prompt from a file.
    """
    with open(COMPILATION_REPAIR_PROMPT_FILE, "r") as f:
        prompt = f.read()

    return prompt.strip()


def read_conversation_file(
    conversation_file: Path,
) -> List[Dict]:
    """
    Read the conversation file and return a list of messages.
    Args:
        conversation_file (Path): The path to the conversation file.
    Returns:
        List[Dict]: A list of messages in the conversation.
    """
    with open(conversation_file, "r") as f:
        conversations = json.load(f)
    return conversations


def make_unified_diff(
    original: str,
    modified: str,
    out_path: Path | None = None,
) -> str:
    """
    Produce a unified diff between original and modified texts suitable for prompting.

    This implementation uses the system `diff -uw` command. Both inputs are
    written to temporary files and `diff -uw` is invoked to produce the unified
    diff while ignoring whitespace differences.

    Returns the diff as a single string (may be empty).
    """
    # Write to temporary files
    f1 = tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8")
    f2 = tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8")
    try:
        # If requested, we still let diff -w handle whitespace normalization; so
        # we write the raw contents.
        f1.write(original)
        f2.write(modified)
        f1.flush()
        f2.flush()
        f1.close()
        f2.close()

        cmd = ["diff", "-uw", f1.name, f2.name]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        diff_out = proc.stdout
        if out_path is not None:
            Path(out_path).write_text(diff_out)
        return diff_out
    finally:
        try:
            os.unlink(f1.name)
        except Exception:
            pass
        try:
            os.unlink(f2.name)
        except Exception:
            pass


def write_conversation_file(
    conversations: List[Dict],
    conversation_file: Path,
) -> None:
    """
    Write the conversation to a file.
    Args:
        conversation_file (Path): The path to the conversation file.
        conversations (List[Dict]): The conversation to write to the file.
    """
    with open(conversation_file, "w") as f:
        json.dump(conversations, f, indent=4)


def count_tokens(
    content: str,
    model: str = "gpt-4o",
) -> int:
    """
    Count the number of tokens in the content based on the model.
    Args:
        content (str): The content to count tokens for.
        model (str): The model to use for token counting.
    Returns:
        int: The number of tokens in the content.
    """

    if model.startswith("gpt-4"):
        encoding = tiktoken.encoding_for_model("gpt-4")
    elif model.startswith("deepseek"):
        encoding = tiktoken.encoding_for_model("deepseek-chat")
    else:
        raise ValueError(
            f"Unknown model: {model}. Supported models: gpt-4, gpt-3.5, deepseek-chat."
        )

    return len(encoding.encode(content))
