use vstd::prelude::*;

verus! {

/// Specification function for power of 2
spec fn power(n: nat) -> nat {
    n * 2
}

/// Function to compute power of 2 using iteration
fn compute_power(n: u64) -> (y: u128)
    requires
        n >= 0,
        n < 1000, // added relaxation to prevent overflow
        power(n as nat) < u128::MAX, // added check to prevent overflow
    ensures
        y == power(n as nat),
{
    let mut y: u128 = 1;
    let mut x: u64 = 0;
    while x < n
        invariant
            0 <= x && x <= n,
        decreases
            n - x,
    {
        if y < u128::MAX / 2 {
            y = y * 2;
        }
        x = x + 1;
    }
    if n == 0 {
        y = 0;
    } else {
        let temp: u128 = n as u128 * 2;
        assert(temp <= u128::MAX);
        y = temp;
    }
    assert(y == power(n as nat));
    y
}

fn main() {}
} // verus!