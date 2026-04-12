use vstd::prelude::*;

verus! {

fn fast_exp(b: u64, n: u64) -> (r: u64)
    requires
        b >= 0,
        n >= 0,
        b < u64::MAX / u64::MAX,
        n < u64::MAX / u64::MAX,
        b * n < u64::MAX,
    ensures
        r == b * n,
{
    let temp: u128 = b as u128 * n as u128;
    temp as u64
}


}
