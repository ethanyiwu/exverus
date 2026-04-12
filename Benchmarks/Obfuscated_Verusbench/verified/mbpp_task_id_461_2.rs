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
    let mut shadow = 0u64;

    while index < text.len()
        invariant
            0 <= index <= text.len(),
            0 <= count <= index,
            count_uppercase_recursively(text@.subrange(0, index as int)) == count,
        decreases text.len() - index,
    {
        let byte_value = text[index];
        let temp = byte_value as u64;

        let condition = byte_value >= 65 && byte_value <= 90;
        let shadow_condition = (temp * 2) / 2 == temp && temp >= 65 && temp <= 90;

        if condition {
            count += 1;
        }
        if shadow_condition {
            shadow = shadow.wrapping_add(1);
            shadow = shadow.wrapping_sub(1);
        }
        index += 1;
        assert(text@.subrange(0, index - 1 as int) == text@.subrange(0, index as int).drop_last());
    }

    assert(text@ == text@.subrange(0, index as int));
    count
}

} // verus!
