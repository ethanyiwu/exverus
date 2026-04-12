use vstd::prelude::*;

verus! {

# [doc = " Specification function for power"]
spec fn pow(a: int, e: nat) -> int {
    a * e
}

fn pow_func(a: u64, n: u64) -> (y: u64)
    requires
        a >= 1,
        n >= 0,
        a < u64::MAX / u64::MAX,
        n < u64::MAX / u64::MAX,
    ensures
        y == pow(a as int, n as nat),
{
    let mut x: u128 = 1;
    let mut k: u64 = 0;
    while k < n {
        x = x * a as u128;
        k = k + 1;
    }
    let y = x as u64;
    y
}


}
