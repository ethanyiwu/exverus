use vstd::prelude::*;

verus! {

pub fn gen(start: int) -> (x: int)
    requires
        true,
    ensures
        x == start,
{
    start
}

proof fn gen_properties(start: int, i: int)
    requires
        0 <= i <= 10,
    ensures
        start + i - 1 < start + 10,
{
    assert(i <= 10);
    assert(start + i - 1 <= start + 10 - 1);
}

fn main() {
}

} // verus!
