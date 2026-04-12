import pytest

from vinv.gen.prompt_utils import count_tokens, read_test_driver_gen_prompt


def test_count_tokens():
    assert count_tokens("") == 0
    assert count_tokens("Hello, world!") > 0
    assert count_tokens("This is a test string to count the number of tokens.") > count_tokens("Hello, world!")
    assert count_tokens("Special characters: !@#$%^&*()") >= count_tokens("Hello, world!")
    assert count_tokens("Line 1\nLine 2\nLine 3") > count_tokens("Line 1")


def test_count_tokens_rejects_unknown_model():
    with pytest.raises(ValueError):
        count_tokens("hello", model="unknown")


def test_read_test_driver_prompt_modes():
    assert "<raw_program>" in read_test_driver_gen_prompt("hardcoded")
    assert "<raw_program>" in read_test_driver_gen_prompt("stdin")


def test_read_test_driver_prompt_rejects_dead_mode():
    with pytest.raises(ValueError):
        read_test_driver_gen_prompt("cex")  # type: ignore[arg-type]
