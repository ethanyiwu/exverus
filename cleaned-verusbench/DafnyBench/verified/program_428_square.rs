use vstd::prelude::*;

verus! {

/// Specification function for square
spec fn square(n: nat) -> nat {
    n * n
}

/// Function to calculate square
fn square_func(n: u64) -> (sqn: u64)
    requires
        n >= 0,
        n < 1000000,  // added a limit to prevent overflow
        n * n < u64::MAX,  // added a check to prevent overflow

    ensures
        sqn == square(n as nat),
{
    let temp: u128 = n as u128 * n as u128;
    assert(temp <= u64::MAX as u128);
    let sqn: u64 = temp as u64;
    sqn
}

fn main() {
}

} // verus!
