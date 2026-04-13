import pytest
from jinja2 import UndefinedError

from vinv.gen.prompt_utils import count_tokens, render_prompt


def test_count_tokens():
    assert count_tokens("") == 0
    assert count_tokens("Hello, world!") > 0
    assert count_tokens("This is a test string to count the number of tokens.") > count_tokens("Hello, world!")
    assert count_tokens("Special characters: !@#$%^&*()") >= count_tokens("Hello, world!")
    assert count_tokens("Line 1\nLine 2\nLine 3") > count_tokens("Line 1")


def test_count_tokens_rejects_unknown_model():
    with pytest.raises(ValueError):
        count_tokens("hello", model="unknown")


def test_render_prompt_requires_j2():
    with pytest.raises(ValueError):
        render_prompt("iterative/naive_repair.txt")


def test_render_prompt_uses_jinja_templates():
    rendered = render_prompt(
        "iterative/naive_repair.j2",
        buggy_proof="buggy",
        original_proof="original",
        error_message="boom",
    )
    assert "buggy" in rendered
    assert "original" in rendered
    assert "boom" in rendered


def test_render_prompt_rejects_missing_context():
    with pytest.raises(UndefinedError):
        render_prompt("iterative/compilation_repair.j2", proof_content="buggy")
