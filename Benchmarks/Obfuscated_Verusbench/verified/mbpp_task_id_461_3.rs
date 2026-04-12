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

fn check_upper(c: u8) -> (b: bool)
    ensures
        b == is_upper_case(c),
{
    (c >= 65) && (c <= 90)
}

fn count_uppercase(text: &[u8]) -> (count: u64)
    ensures
        0 <= count <= text.len(),
        count_uppercase_recursively(text@) == count,
{
    let mut pos = 0;
    let mut total = 0;
    let mut tracker = 0u64;

    while pos < text.len()
        invariant
            0 <= pos <= text.len(),
            0 <= total <= pos,
            count_uppercase_recursively(text@.subrange(0, pos as int)) == total,
        decreases text.len() - pos,
    {
        let current_char = text[pos];
        let mut inner = 0;

        while inner < 1
            invariant
            decreases 1 - inner,
        {
            inner = inner + 1;
        }

        let is_upper = check_upper(current_char);
        if is_upper {
            total = total + 1;
        }
        pos = pos + 1;
        tracker = pos as u64;
        assert(text@.subrange(0, pos - 1 as int) == text@.subrange(0, pos as int).drop_last());
    }
    assert(text@ == text@.subrange(0, pos as int));
    total
}

} // verus!
