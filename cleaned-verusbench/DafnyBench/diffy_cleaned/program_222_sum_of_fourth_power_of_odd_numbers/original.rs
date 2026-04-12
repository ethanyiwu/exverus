use vstd::prelude::*;

verus! {

# [doc = " Function to calculate the sum of the fourth power of odd numbers"]
fn sum_of_fourth_power_of_odd_numbers(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < 1000,
        n < u64::MAX / u64::MAX,
    ensures
        sum == n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15,
{
    let mut sum: u128 = 0;
    let mut i: u64 = 1;
    for k in 0..n {
        sum = sum + (i as u128) * (i as u128) * (i as u128) * (i as u128);
        i = i + 2;
    }
    sum as u64
}


}
