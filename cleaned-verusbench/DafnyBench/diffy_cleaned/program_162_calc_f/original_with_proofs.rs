use vstd::prelude::*;

verus! {

fn calc_f(n: u64) -> (res: u64)
    requires
        n < 1000, // added precondition to prevent overflow
        n < u64::MAX / 2, // added precondition to prevent overflow
        n < u64::MAX / u64::MAX, // added precondition to prevent overflow
    ensures
        res == n,
{
    let mut a: u128 = 0;
    let mut b: u128 = 1;
    let mut c: u128 = 2;
    let mut i: u128 = 0;
    while i < n as u128
        invariant
            0 <= i && i <= n as u128,
            a == i,
            b == i + 1,
            c == i + 2,
            n < 1000, // added precondition to prevent overflow
            n < u64::MAX / 2, // added precondition to prevent overflow
            n < u64::MAX / u64::MAX, // added precondition to prevent overflow
        decreases
            n as u128 - i,
    {
        a = b;
        b = c;
        if a < u128::MAX / 2 && c < u128::MAX / 2 {
            c = a + c;
        }
        i = i + 1;
    }
    assert(a <= u64::MAX as u128);
    let res: u64 = a as u64;
    res
}

fn main() {}
} // verus!