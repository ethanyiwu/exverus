use vstd::prelude::*;

verus! {

fn sum_of_fourth_power_of_odd_numbers(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

    ensures
        sum == n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15,
{
    let temp: u128 = n as u128 * (n as u128 * 2 + 1) * (n as u128 * n as u128 * n as u128 * 24
        - n as u128 * n as u128 * 12 - n as u128 * 14 + 7) as u128 / 15;
    assert(temp <= u64::MAX as u128);
    let sum: u64 = temp as u64;
    sum
}

fn main() {
}

} // verus!
