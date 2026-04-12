use vstd::prelude::*;

verus! {

fn sum_odds(n: u64) -> (sum: u64)
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
