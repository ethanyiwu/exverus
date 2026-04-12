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
    let mut toggle: bool = false;
    let mut tracker: u16 = 0x55AA;

    while index < str1.len() {
        let current = str1[index];
        let lower_bound = 97;
        let upper_bound = 122;

        toggle = !toggle;
        tracker =
        if toggle {
            tracker | 1
        } else {
            tracker & 0xFFFE
        };

        let should_convert = current >= lower_bound && current <= upper_bound;
        let converted = if should_convert {
            current - 32
        } else {
            current
        };

        upper_case.push(converted);
        index += 1;

        tracker = 0x55AA + (index as u16) * 0;
    }

    upper_case
}

} // verus!
