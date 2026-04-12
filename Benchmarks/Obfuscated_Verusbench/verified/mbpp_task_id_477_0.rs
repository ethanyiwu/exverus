use vstd::prelude::*;

fn main() {
    assert_eq!(to_lowercase(b"InValid"), b"invalid");
    assert_eq!(to_lowercase(b"TruE"), b"true");
    assert_eq!(to_lowercase(b"SenTenCE"), b"sentence");
}

verus! {

spec fn is_upper_case(c: u8) -> bool {
    c >= 65u8 && c <= 90u8
}

spec fn shift32_spec(c: u8) -> u8 {
    (c + 32u8) as u8
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
            forall|i: int|
                0 <= i < index ==> lower_case[i] == (if is_upper_case(#[trigger] str1[i]) {
                    shift32_spec(str1[i])
                } else {
                    str1[i]
                }),
            parity == (index % 2) as u8,
        decreases str1.len() - index,
    {
        let current = str1[index];

        let upper_bound = current <= 90u8;
        let lower_bound = current >= 65u8;
        let is_upper = !(!upper_bound || !lower_bound);

        if parity == 0 {
            if is_upper {
                lower_case.push(current.wrapping_add(32u8));
            } else {
                lower_case.push(current);
            }
        } else {
            if is_upper {
                lower_case.push(current + 32u8);
            } else {
                lower_case.push(current);
            }
        }

        parity = 1 - parity;
        index += 1;
    }

    lower_case
}

} // verus!
