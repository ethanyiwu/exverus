use vstd::prelude::*;

fn to_uppercase(str1: &[u8]) -> Vec<u8> {
    let mut upper_case: Vec<u8> = Vec::with_capacity(str1.len());
    let mut pos: i32 = -1;
    let mut tracker: u16 = 0;

    while pos < (str1.len() as i32) - 1 {
        pos += 1;
        let index: usize = pos as usize;
        let current: u8 = str1[index];

        let lower_bound: bool = (current as i32).wrapping_sub(97) >= 0;
        let upper_bound: bool = (122 as i32).wrapping_sub(current as i32) >= 0;
        let should_shift: bool = lower_bound && upper_bound;

        if should_shift {
            upper_case.push(current.wrapping_sub(32));
        } else {
            upper_case.push(current);
        }

        tracker = tracker.wrapping_add(current as u16);
    }

    upper_case
}

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

} // verus!
