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
    let mut index = 0;
    let mut parity = false;

    while index < text.len() {
        let current = text[index];
        parity = !parity;

        if !is_digit(current) {
            return false;
        }
        index += 1;
    }
    true
}

} // verus!
