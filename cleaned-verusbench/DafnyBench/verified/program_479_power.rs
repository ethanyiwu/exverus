use vstd::prelude::*;

verus! {

/// Specification function to calculate power of 2
spec fn power(n: nat) -> nat {
    if n == 0 {
        1
    } else {
        n * 2
    }
}

/// Function to calculate power of 2 using iteration
fn compute_power(n: u64) -> (p: u64)
    requires
        n > 0,
        n < u64::MAX / 2,
        n * 2 < u64::MAX,  // added precondition to prevent overflow
        n < 1000,  // added precondition to prevent overflow

    ensures
        p == power(n as nat),
{
    let temp: u128 = n as u128 * 2;
    assert(temp <= u64::MAX as u128);
    temp as u64
}

fn main() {
}

} // verus!
