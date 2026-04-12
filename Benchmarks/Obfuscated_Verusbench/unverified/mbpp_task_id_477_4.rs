use vstd::prelude::*;

fn main() {
    assert_eq!(to_lowercase(b"InValid"), b"invalid");
    assert_eq!(to_lowercase(b"TruE"), b"true");
    assert_eq!(to_lowercase(b"SenTenCE"), b"sentence");
}

verus! {

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
    let mut index = 0;
    let mut flip = false;
    let mut tracker = 0u8;

    while index < str1.len() {
        let current = str1[index];
        let upper_check = current >= 65 && current <= 90;
        let alt_check = !(current < 65) && !(current > 90);

        if flip {
            lower_case.push(
                if upper_check {
                    current + 32
                } else {
                    current
                },
            );
        } else {
            let converted = if alt_check {
                current + 32
            } else {
                current
            };
            lower_case.push(converted);
        }

        tracker = current & 3;
        flip = !flip;
        index += 1;
    }

    lower_case
}

spec fn is_upper_case(c: u8) -> bool {
    c >= 65 && c <= 90
}

spec fn shift32_spec(c: u8) -> u8 {
    (c + 32) as u8
}

} // verus!
