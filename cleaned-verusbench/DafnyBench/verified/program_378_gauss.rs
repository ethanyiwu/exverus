use vstd::prelude::*;

verus! {

fn gauss(n: u64) -> (sum: u64)
    requires
        n >= 0,
        n < 1000000,  // added condition to ensure n is not too large
        n * (n + 1) < u64::MAX,  // added condition to ensure multiplication does not overflow
        n * (n + 1) / 2
            < u64::MAX,  // added condition to ensure division does not overflow

    ensures
        sum == n * (n + 1) / 2,
{
    let temp1: u128 = n as u128 * (n as u128 + 1) as u128;
    assert(temp1 <= u64::MAX as u128);
    let temp2: u128 = temp1 / 2;
    assert(temp2 <= u64::MAX as u128);
    let sum: u64 = temp2 as u64;
    sum
}

fn sum_odds(n: u64) -> (sum: u64)
    requires
        n < 1000000,  // added condition to ensure n is not too large
        n * n
            < u64::MAX,  // added condition to ensure multiplication does not overflow

    ensures
        sum == n * n,
{
    let temp: u128 = n as u128 * n as u128;
    assert(temp <= u64::MAX as u128);
    let sum: u64 = temp as u64;
    sum
}

fn main() {
}

} // verus!
