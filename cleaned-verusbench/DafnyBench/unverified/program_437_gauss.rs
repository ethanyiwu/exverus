use vstd::prelude::*;

verus! {

# [doc = " Function to calculate the sum of numbers from 1 to n using Gauss' formula"]
fn gauss(n: u64) -> (sum: u64)
    requires
        n >= 0,
        n * (n + 1) / 2 <= u64::MAX,
    ensures
        sum == n * (n + 1) / 2,
{
    let temp: u128 = n as u128 * (n as u128 + 1) / 2;
    let sum: u64 = temp as u64;
    sum
}

# [doc = " Function to calculate the sum of the first n odd numbers"]
fn sum_odds(n: u64) -> (sum: u64)
    requires
        n >= 0,
        n * n <= u64::MAX,
    ensures
        sum == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    let sum: u64 = temp as u64;
    sum
}


}
