use vstd::prelude::*;

verus! {

/// Adds two natural numbers by incrementing the first number.
fn add_by_inc(x: u64, y: u64) -> (z: u64)
    requires
        x + y < u64::MAX,
        y < u64::MAX / 2,
    ensures
        z == x + y,
{
    let mut z = x;
    let mut i = 0;
    while i < y && z < u64::MAX - 1
        invariant
            0 <= i <= y,
            z == x + i,
        decreases y - i,
    {
        assert(z < u64::MAX);
        z = z + 1;
        i = i + 1;
    }
    assert(i == y);
    z
}

fn main() {
}

} // verus!
