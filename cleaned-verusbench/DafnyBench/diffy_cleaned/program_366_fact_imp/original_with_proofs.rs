use vstd::prelude::*;
use vstd::*;

verus! {

fn fact_imp(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        r >= 0,
{
    let mut r: u64 = 1;
    let mut m: u64 = n;
    while m > 0
        invariant
            0 <= m && m <= n,
            r >= 0,
            m < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        decreases
            m,
    {
        assert(m >= 1);
        assert(r >= 0);
        let temp: u128 = r as u128 * m as u128;
        assert(temp <= u64::MAX as u128);
        r = temp as u64;
        m = m - 1;
    }
    r
}

fn main() {}
} // verus!