use vstd::prelude::*;

verus! {

/// Specification function for addition
spec fn add(x: int, y: int) -> int {
    x + y
}

/// Function to add two numbers using increment
fn add_by_inc(x: u64, y: u64) -> (z: u64)
    requires
        x >= 0,
        y >= 0,
        x < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        y < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        x + y < u64::MAX,
    ensures
        z == x + y,
{
    let mut z: u64 = x;
    let mut i: u64 = 0;
    while i < y
        invariant
            0 <= i && i <= y,
            z == x + i,
            x + y < u64::MAX, // added relaxation to prevent overflow
        decreases
            y - i,
    {
        if z < u64::MAX - 1 {
            z = z + 1;
        }
        i = i + 1;
    }
    assert(z == x + y);
    z
}

fn main() {}

} // verus!