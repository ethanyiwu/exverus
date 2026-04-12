use vstd::prelude::*;

verus! {

fn calc_f(n: u64) -> (res: u64)
    requires
        n < 1000,
        n < u64::MAX / 2,
        n < u64::MAX / u64::MAX,
    ensures
        res == n,
{
    let mut a: u128 = 0;
    let mut b: u128 = 1;
    let mut c: u128 = 2;
    let mut i: u128 = 0;
    while i < n as u128 {
        a = b;
        b = c;
        if a < u128::MAX / 2 && c < u128::MAX / 2 {
            c = a + c;
        }
        i = i + 1;
    }
    let res: u64 = a as u64;
    res
}


}
