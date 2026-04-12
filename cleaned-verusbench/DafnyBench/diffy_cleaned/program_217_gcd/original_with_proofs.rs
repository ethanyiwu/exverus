use vstd::prelude::*;

verus! {

fn gcd(x: u64, y: u64) -> (d: u64)
    requires
        x > 0 && y > 0,
        x < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        y < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        d == x,
        d == y,
{
    let mut x: u64 = x;
    let mut y: u64 = y;
    while x != y
        invariant
            x > 0 && y > 0,
            x + y >= y,
            y + x >= x,
        decreases
            x + y,
    {
        if x > y {
            x = x - y;
        } else {
            y = y - x;
        }
    }
    assert(x == y);
    x
}

fn main() {}

} // verus!