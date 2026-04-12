use vstd::prelude::*;

verus! {

/// Function to calculate the sum of odd numbers up to n
fn sum_odds(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < 10000,  // Adding a precondition to limit the value of n
        n * n < u64::MAX,  // Adding a precondition to prevent overflow

    ensures
        sum == n * n,
{
    let sum: u64 = n * n;
    sum
}

fn main() {
}

} // verus!
