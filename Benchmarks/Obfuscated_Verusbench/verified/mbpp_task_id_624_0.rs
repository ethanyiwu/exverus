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

fn should_shift_char(byte_val: u8) -> (b: bool)
    ensures
        b == (byte_val >= 97 && byte_val <= 122),
{
    let lower_bound = byte_val >= 97;
    let upper_bound = byte_val <= 122;
    lower_bound && upper_bound
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
    let mut position: usize = 0;
    let mut parity_flag: bool = true;

    while position < str1.len()
        invariant
            0 <= position <= str1.len(),
            upper_case.len() == position,
            forall|i: int|
                0 <= i < position ==> (upper_case[i] == (if is_lower_case(#[trigger] str1[i]) {
                    shift_minus_32_spec(str1[i])
                } else {
                    str1[i]
                })),
        decreases str1.len() - position,
    {
        let current_byte = str1[position];

        let needs_conversion = should_shift_char(current_byte);
        let transformed_byte = if needs_conversion {
            current_byte - 32
        } else {
            current_byte
        };

        upper_case.push(transformed_byte);

        parity_flag =
        if parity_flag {
            false
        } else {
            true
        };
        position = position + 1;
    }

    upper_case
}

} // verus!
