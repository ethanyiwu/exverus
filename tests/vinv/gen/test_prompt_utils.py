import pytest

from vinv.gen.prompt_utils import count_tokens


def test_count_tokens():
    assert count_tokens("") == 0
    assert count_tokens("Hello, world!") > 0
    assert count_tokens("This is a test string to count the number of tokens.") > count_tokens("Hello, world!")
    assert count_tokens("Special characters: !@#$%^&*()") >= count_tokens("Hello, world!")
    assert count_tokens("Line 1\nLine 2\nLine 3") > count_tokens("Line 1")


def test_count_tokens_rejects_unknown_model():
    with pytest.raises(ValueError):
        count_tokens("hello", model="unknown")
