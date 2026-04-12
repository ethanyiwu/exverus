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
    let mut index = 0;

    while index < str1.len()
        invariant
            0 <= index <= str1.len(),
            upper_case.len() == index,
            forall|i: int|
                0 <= i < index ==> (upper_case[i] == (if is_lower_case(#[trigger] str1[i]) {
                    shift_minus_32_spec(str1[i])
                } else {
                    str1[i]
                })),
        decreases str1.len() - index,
    {
        let current = str1[index];
        let is_lower = (current as i32 - 97) >= 0 && (122 - current as i32) >= 0;

        if is_lower {
            upper_case.push(current - 32);
        } else {
            upper_case.push(current);
        }

        index += 1;
    }

    upper_case
}

} // verus!
