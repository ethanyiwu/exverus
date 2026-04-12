use vstd::prelude::*;

verus! {

fn compute_fusc(n: u64) -> (b: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX,
        n < 100000,
    ensures
        b == n,
{
    let mut b: u64 = n;
    b
}


}
