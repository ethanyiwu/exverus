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
    let mut shadow: usize = str1.len();
    let mut state: u16 = 0;

    while index < str1.len()
        invariant
            shadow == str1.len() - index,
            lower_case.len() == index,
            forall|i: int|
                0 <= i < index ==> lower_case[i] == (if is_upper_case(#[trigger] str1[i]) {
                    shift32_spec(str1[i])
                } else {
                    str1[i]
                }),
        decreases str1.len() - index,
    {
        let c = str1[index];
        state = state.wrapping_add(c as u16).wrapping_sub(index as u16);

        let condition = !(c < 65) && !(c > 90);
        let transformed = if condition {
            (c + 32) as u8
        } else {
            c
        };

        lower_case.push(transformed);
        index += 1;
        shadow -= 1;
    }

    lower_case
}

} // verus!
