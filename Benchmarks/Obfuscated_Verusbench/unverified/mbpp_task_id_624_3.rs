use vstd::prelude::*;

fn main() {
    assert_eq!(to_uppercase(b"person"), b"PERSON");
    assert_eq!(to_uppercase(b"final"), b"FINAL");
    assert_eq!(to_uppercase(b"Valid"), b"VALID");
}

verus! {

spec fn is_lower_case(c: u8) -> bool {
    c >= 97 && c <= 122
}

spec fn shift_minus_32_spec(c: u8) -> u8 {
    (c - 32) as u8
}

fn to_uppercase(str1: &[u8]) -> (result: Vec<u8>)
    ensures
        str1@.len() == result@.len(),
        forall|i: int|
            0 <= i < str1.len() ==> (result[i] == (if is_lower_case(#[trigger] str1[i]) {
                shift_minus_32_spec(str1[i])
            } else {
                str1[i]
            })),
{
    let mut upper_case: Vec<u8> = Vec::with_capacity(str1.len());
    let mut index: usize = 0;
    let mut reverse_index: usize = str1.len();
    let mut accumulator: u16 = 0x55AA;

    while index < str1.len() {
        let current_char = str1[index];
        let is_lower = current_char >= 97 && current_char <= 122;

        if is_lower {
            upper_case.push(current_char - 32);
        } else {
            upper_case.push(current_char);
        }

        accumulator = (accumulator + current_char as u16) - current_char as u16;
        reverse_index = reverse_index - 1;
        index = index + 1;
    }

    upper_case
}

} // verus!
