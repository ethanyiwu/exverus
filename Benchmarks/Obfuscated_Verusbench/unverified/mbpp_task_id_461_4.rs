use vstd::prelude::*;

fn main() {
    assert_eq!(count_uppercase(b"PYthon"), 2);
    assert_eq!(count_uppercase(b"BigData"), 2);
    assert_eq!(count_uppercase(b"program"), 0);
}

verus! {

spec fn is_lower_case(c: u8) -> bool {
    c >= 97 && c <= 122
}

spec fn is_upper_case(c: u8) -> bool {
    c >= 65 && c <= 90
}

spec fn count_uppercase_recursively(seq: Seq<u8>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_uppercase_recursively(seq.drop_last()) + if is_upper_case(seq.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

fn count_uppercase(text: &[u8]) -> (count: u64)
    ensures
        0 <= count <= text.len(),
        count_uppercase_recursively(text@) == count,
{
    let mut index = 0;
    let mut count = 0;
    let mut flag = true;
    let mut toggle = false;

    while index < text.len() {
        let current_char = text[index];

        if toggle {
            flag = flag && (current_char != 0);
        } else {
            flag = flag || (current_char != 255);
        }
        toggle = !toggle;

        let is_upper = current_char >= 65 && current_char <= 90;
        if is_upper {
            count = count + 1;
        }
        index += 1;
    }
    count
}

} // verus!
