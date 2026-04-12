use vstd::prelude::*;

verus! {

# [doc = " Specification function to calculate power of 2"]
spec fn power(n: nat) -> nat {
    if n == 0 {
        1
    } else {
        n * 2
    }
}

# [doc = " Function to calculate power of 2 using iteration"]
fn compute_power(n: u64) -> (p: u64)
    requires
        n > 0,
        n < u64::MAX / 2,
        n * 2 < u64::MAX,
        n < 1000,
    ensures
        p == power(n as nat),
{
    let temp: u128 = n as u128 * 2;
    temp as u64
}


}
