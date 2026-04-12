use vstd::prelude::*;

fn main() {
    assert_eq!(to_lowercase(b"InValid"), b"invalid");
    assert_eq!(to_lowercase(b"TruE"), b"true");
    assert_eq!(to_lowercase(b"SenTenCE"), b"sentence");
}

verus! {

spec fn is_upper_case(c: u8) -> bool {
    c >= 65 && c <= 90
}

spec fn shift32_spec(c: u8) -> u8 {
    (c + 32) as u8
}

fn to_lowercase(str1: &[u8]) -> (result: Vec<u8>)
    ensures
        str1@.len() == result@.len(),
        forall|i: int|
            0 <= i < str1.len() ==> result[i] == (if is_upper_case(#[trigger] str1[i]) {
                shift32_spec(str1[i])
            } else {
                str1[i]
            }),
{
    let mut lower_case: Vec<u8> = Vec::with_capacity(str1.len());
    let mut index: usize = 0;
    let mut parity: u8 = 0;

    while index < str1.len()
        invariant
            0 <= index <= str1.len(),
            lower_case.len() == index,
            parity == (index % 2) as u8,
            forall|i: int|
                0 <= i < index ==> lower_case[i] == (if is_upper_case(#[trigger] str1[i]) {
                    shift32_spec(str1[i])
                } else {
                    str1[i]
                }),
        decreases str1.len() - index,
    {
        let current_char = str1[index];
        let base_a: u8 = 65;
        let base_z: u8 = 90;
        let shift_amount: u8 = 32;

        let check_lower = current_char < base_a;
        let check_upper = current_char > base_z;
        let is_not_upper = check_lower || check_upper;

        let transformed_char = if is_not_upper {
            current_char
        } else {
            let temp = current_char as u16;
            let shifted = temp + shift_amount as u16;
            shifted as u8
        };

        lower_case.push(transformed_char);
        index = index + 1;
        parity = (parity + 1) % 2;
    }

    lower_case
}

} // verus!
