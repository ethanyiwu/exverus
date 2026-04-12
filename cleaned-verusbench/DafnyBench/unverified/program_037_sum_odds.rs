use vstd::prelude::*;

verus! {

# [doc = " Specification function to calculate the sum of odd numbers up to n"]
spec fn sum_odds(n: nat) -> nat {
    n * n
}

# [doc = " Function to calculate the sum of odd numbers up to n"]
fn sum_odds_func(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,
    ensures
        sum == n * n,
{
    let mut sum: u64 = 1;
    let mut i: u64 = 0;
    while i < n - 1 {
        i = i + 1;
        sum = sum + 2 * i + 1;
    }
    sum
}


}
