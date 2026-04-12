use vstd::prelude::*;

verus! {

# [doc = " Specification function for square"]
spec fn square(n: nat) -> nat {
    n * n
}

# [doc = " Function to calculate square"]
fn square_func(n: u64) -> (sqn: u64)
    requires
        n >= 0,
        n < 1000000,
        n * n < u64::MAX,
    ensures
        sqn == square(n as nat),
{
    let temp: u128 = n as u128 * n as u128;
    let sqn: u64 = temp as u64;
    sqn
}


}
