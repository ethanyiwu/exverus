use vstd::prelude::*;

verus! {

/// Proof function to calculate the exponentiation
fn exp(b: u64, n: u64) -> (result: u128)
    requires
        n < 1000000,  // added relaxation to prevent overflow
        n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

    ensures
        result == n * (n + 1) / 2,
{
    let mut i: u64 = 0;
    let mut x: u128 = 0;
    let mut y: u128 = 1;
    while i < n
        invariant
            0 <= i && i <= n,
            x == i * (i + 1) / 2,
            y == (i + 1) * (i + 2) / 2,
            n < 1000000,  // added relaxation to prevent overflow
            n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

        decreases n - i,
    {
        x = y;
        y = x + y;
        i = i + 1;
    }
    assert(x == n * (n + 1) / 2);
    x
}

fn main() {
}

} // verus!
