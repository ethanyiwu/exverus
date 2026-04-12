use vstd::prelude::*;

verus! {

fn sum_of_fourth_power_of_odd_numbers(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,
    ensures
        sum == n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15,
{
    let mut sum: u64 = 0;
    let mut i: u64 = 1;
    let mut k: u64 = 0;
    while k < n {
        let temp: u128 = sum as u128 + i as u128 * i as u128 * i as u128 * i as u128;
        sum = temp as u64;
        i = i + 2;
        k = k + 1;
    }
    sum
}


}
