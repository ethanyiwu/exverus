use vstd::prelude::*;

verus! {

fn gauss(n: u64) -> (sum: u64)
    requires
        n >= 0,
        n < 1000000,
        n * (n + 1) < u64::MAX,
        n * (n + 1) / 2 < u64::MAX,
    ensures
        sum == n * (n + 1) / 2,
{
    let temp1: u128 = n as u128 * (n as u128 + 1) as u128;
    let temp2: u128 = temp1 / 2;
    let sum: u64 = temp2 as u64;
    sum
}

fn sum_odds(n: u64) -> (sum: u64)
    requires
        n < 1000000,
        n * n < u64::MAX,
    ensures
        sum == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    let sum: u64 = temp as u64;
    sum
}


}
