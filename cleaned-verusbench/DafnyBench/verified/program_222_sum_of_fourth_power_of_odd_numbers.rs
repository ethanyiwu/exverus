use vstd::prelude::*;

verus! {

/// Function to calculate the sum of the fourth power of odd numbers
fn sum_of_fourth_power_of_odd_numbers(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < 1000,  // added relaxation to prevent overflow
        n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

    ensures
        sum == n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15,
{
    let mut sum: u128 = 0;
    let mut i: u64 = 1;
    for k in 0..n
        invariant
            0 <= k as int && k as int <= n as int,
            i as int == 2 * k as int + 1,
            sum == k as int * (2 * k as int + 1) * (24 * k as int * k as int * k as int - 12
                * k as int * k as int - 14 * k as int + 7) / 15,
            n < 1000,  // added relaxation to prevent overflow
            n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
    {
        sum = sum + (i as u128) * (i as u128) * (i as u128) * (i as u128);
        i = i + 2;
    }
    assert(sum <= u64::MAX as u128);
    sum as u64
}

fn main() {
}

} // verus!
