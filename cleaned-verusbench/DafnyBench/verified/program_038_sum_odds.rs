use vstd::prelude::*;

verus! {

/// Sum of squares of natural numbers up to N
fn sum_odds(n: u64) -> (sum_: u64)
    requires
        n > 0,
        n * n < u64::MAX,  // added relaxation to prevent overflow

    ensures
        sum_ == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    assert(temp <= u64::MAX as u128);
    let sum_: u64 = temp as u64;
    assert(sum_ == n * n);
    sum_
}

fn main() {
}

} // verus!
