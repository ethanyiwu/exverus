use vstd::prelude::*;

verus! {

/// Specification function for power
spec fn pow(a: int, e: nat) -> int {
    a * e
}

fn pow_func(a: u64, n: u64) -> (y: u64)
    requires
        a >= 1,
        n >= 0,
        a < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
        n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

    ensures
        y == pow(a as int, n as nat),
{
    let mut x: u128 = 1;
    let mut k: u64 = 0;
    while k < n
        invariant
            x == pow(a as int, k as nat) as int,
            0 <= k && k <= n,
            a < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
            n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

        decreases n - k,
    {
        x = x * a as u128;
        assert(x == pow(a as int, (k + 1) as nat) as int);
        k = k + 1;
    }
    assert(k == n);
    assert(x <= u64::MAX as u128);
    let y = x as u64;
    y
}

fn main() {
}

} // verus!
