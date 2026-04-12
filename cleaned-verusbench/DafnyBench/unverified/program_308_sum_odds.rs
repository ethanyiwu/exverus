use vstd::prelude::*;

verus! {

# [doc = " Function to calculate the sum of odd numbers up to n"]
fn sum_odds(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < 10000,
        n * n < u64::MAX,
    ensures
        sum == n * n,
{
    let mut sum: u64 = n * n;
    sum
}


}
