from pathlib import Path

from vinv.gen.prompt_utils import count_tokens

def test_count_tokens():
    """
    Test the count_tokens function with various inputs.
    """
    # Test with a simple string
    assert count_tokens("Hello, world!") == 4

    # Test with a longer string
    assert count_tokens("This is a test string to count the number of tokens.") == 12

    # Test with an empty string
    assert count_tokens("") == 0

    # Test with a string containing special characters
    assert count_tokens("Special characters: !@#$%^&*()") == 10

    # Test with a multi-line string
    assert count_tokens("Line 1\nLine 2\nLine 3") == 11

    # 1.0 K 
    # assert count_tokens(Path("/zp_vegeta/scratch_sb/juny/research/rust_playground/verus_inv/results/ori/verusbench_misc_remove_all_greater/test_driver_gpt-4o_hardcoded/output.txt").read_text()) == 840

    # 8.0 K
    # assert count_tokens(Path("/zp_vegeta/scratch_sb/juny/research/rust_playground/verus_inv/results/ori/verusbench_diffy_s32if/test_driver_gpt-4o_hardcoded/output.txt").read_text()) == 30182

    # 12 K
    # assert count_tokens(Path("/zp_vegeta/scratch_sb/juny/research/rust_playground/verus_inv/results/ori/verusbench_diffy_s2lif/test_driver_gpt-4o_hardcoded/output.txt").read_text()) == 38578
