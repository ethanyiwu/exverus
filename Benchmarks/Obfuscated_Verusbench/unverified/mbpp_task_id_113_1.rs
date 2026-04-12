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
    let mut index: usize = 0;
    let mut mix: u32 = 0x9E3779B9u32;

    while index < text.len() {
        if !is_digit(text[index]) {
            return false;
        }
        let shift_amount = ((index % 4) as u32) * 8;
        mix = mix ^ ((text[index] as u32) << shift_amount);
        index += 1;

        if (index % 5) == 2 {
            mix = mix ^ 0x13579BDFu32;
        } else {
            mix = mix ^ 0x9E3779B9u32;
        }
    }

    true
}

} // verus!
