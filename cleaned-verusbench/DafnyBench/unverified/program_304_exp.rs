use vstd::prelude::*;

verus! {

# [doc = " Proof function to calculate the exponential"]
fn exp(b: u64, n: u64) -> (result: u64)
    requires
        b >= 0,
        n >= 0,
        b * n < u64::MAX,
    ensures
        result == b * n,
{
    let temp: u128 = b as u128 * n as u128;
    temp as u64
}


}
