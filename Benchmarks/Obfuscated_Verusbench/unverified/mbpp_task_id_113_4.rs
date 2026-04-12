use vstd::prelude::*;

fn main() {
    assert!(!is_integer(b"python"));
    assert!(is_integer(b"1"));
    assert!(is_integer(b"123"));
}

verus! {

spec fn is_digit_sepc(c: u8) -> bool {
    c >= 48 && c <= 57
}

fn is_digit(c: u8) -> (res: bool)
    ensures
        res == is_digit_sepc(c),
{
    c >= 48 && c <= 57
}

fn is_integer(text: &[u8]) -> (result: bool)
    ensures
        result == (forall|i: int| 0 <= i < text.len() ==> (#[trigger] is_digit_sepc(text[i]))),
{
    let mut index = 0usize;
    let mut accumulator = 0u64;
    let mut outcome = true;

    while index < text.len() {
        if !is_digit(text[index]) {
            outcome = false;
        }
        accumulator = accumulator.wrapping_add(1);
        index += 1;
    }

    let mut final_check = 0u8;

    while final_check < 1u8 {
        final_check += 1;
    }

    outcome
}

} // verus!
