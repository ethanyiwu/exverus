use vstd::prelude::*;

verus! {

# [doc = " Sum of squares of natural numbers up to N"]
fn sum_odds(n: u64) -> (sum_: u64)
    requires
        n > 0,
        n * n < u64::MAX,
    ensures
        sum_ == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    let sum_: u64 = temp as u64;
    sum_
}


}
