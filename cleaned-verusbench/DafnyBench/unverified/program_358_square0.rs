use vstd::prelude::*;

verus! {

# [doc = " Function to calculate the square of a number"]
fn square0(n: u64) -> (sqn: u64)
    requires
        n >= 0,
        n * n < u64::MAX,
    ensures
        sqn == n * n,
{
    let mut sqn: u64 = n * n;
    sqn
}


}
