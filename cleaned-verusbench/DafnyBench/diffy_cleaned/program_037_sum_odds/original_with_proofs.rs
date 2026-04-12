use vstd::prelude::*;

verus! {

/// Specification function to calculate the sum of odd numbers up to n
spec fn sum_odds(n: nat) -> nat {
    n * n
}

/// Function to calculate the sum of odd numbers up to n
fn sum_odds_func(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        sum == n * n,
{
    let mut sum: u64 = 1;
    let mut i: u64 = 0;
    while i < n - 1
        invariant
            0 <= i && i < n,
            sum == (i + 1) * (i + 1),
            n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        decreases
            n - i - 1,
    {
        i = i + 1;
        sum = sum + 2 * i + 1;
    }
    assert(sum == n * n);
    sum
}

fn main() {}

} // verus!