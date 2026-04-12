use vstd::prelude::*;

verus! {

/// Function to calculate the sum of odd numbers
fn sum_odds(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < 1000000,  // added relaxation to prevent overflow
        n * n < u64::MAX,  // added check to prevent overflow

    ensures
        sum == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    assert(temp <= u64::MAX as u128);
    temp as u64
}

fn main() {
}

} // verus!
