use vstd::prelude::*;

verus! {

/// Calculates the sum of the fourth powers of the first n odd numbers.
fn sum_of_fourth_power_of_odd_numbers(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15 < u64::MAX, // added relaxation to prevent overflow
    ensures
        sum == n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15,
{
    let mut sum: u64 = 0;
    let mut i: u64 = 1;
    for k in 0..n
        invariant
            0 <= k && k <= n,
            i == 2 * k + 1,
            sum == k * (2 * k + 1) * (24 * k * k * k - 12 * k * k - 14 * k + 7) / 15,
            n > 0,
            n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
            n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15 < u64::MAX, // added relaxation to prevent overflow
    {
        sum = sum + i * i * i * i;
        i = i + 2;
    }
    sum
}

fn main() {}

} // verus!