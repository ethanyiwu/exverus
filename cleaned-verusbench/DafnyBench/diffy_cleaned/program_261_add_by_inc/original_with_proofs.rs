use vstd::prelude::*;

verus! {

fn add_by_inc(x: u64, y: u64) -> (z: u64)
    requires
        x < u64::MAX / 2,
        y < u64::MAX / 2,
    ensures
        z == x + y,
{
    let mut z = x;
    let mut i = 0;
    while i < y
        invariant
            0 <= i && i <= y,
            z == x + i,
            x < u64::MAX / 2,
            y < u64::MAX / 2,
        decreases
            y - i,
    {
        z = z + 1;
        i = i + 1;
    }
    z
}

fn main() {}

} // verus!