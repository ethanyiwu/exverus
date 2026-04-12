use vstd::prelude::*;

verus! {

# [doc = " Function to calculate the sum of odd numbers"]
fn sum_odds(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < 1000000,
        n * n < u64::MAX,
    ensures
        sum == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    temp as u64
}


}
