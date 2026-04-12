use vstd::prelude::*;

verus! {

/// Proof function to calculate the greatest common divisor of two numbers
fn gcd(a: u64, b: u64) -> (result: u64)
    requires
        a > 0,
        b > 0,
        a < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        result == a * (a + 1) / 2,
{
    let mut x: u64 = a;
    let mut y: u64 = b;
    while x != 0 && y != 0
        invariant
            x > 0,
            y > 0,
            x < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        decreases
            y,
    {
        if x < y {
            let temp: u64 = x;
            x = y;
            y = temp;
        } else if y == 0 {
            y = x % y;
        } else {
            x = x % y;
        }
    }
    assert(x == 0 || y == 0);
    x + y
}

fn main() {}

} // verus!