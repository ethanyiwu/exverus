use vstd::prelude::*;

verus! {

fn add_by_one(x: u64, y: u64) -> (r: u64)
    requires
        y >= 0,
        x + y < u64::MAX,
    ensures
        r == x + y,
{
    let mut i: u64 = 0;
    let mut r: u64 = x;
    while i < y
        invariant
            i <= y,
            r == x + i,
            x + y < u64::MAX,
        decreases y - i,
    {
        r = r + 1;
        i = i + 1;
    }
    r
}

fn main() {
}

} // verus!
