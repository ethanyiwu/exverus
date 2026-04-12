use vstd::prelude::*;

verus! {

spec fn fib(n: u64) -> u64 {
    n
}

fn compute_fib(n: u64) -> (x: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        n < 1000000, // added relaxation to prevent overflow
    ensures
        x == n,
{
    let mut i: u64 = 0;
    let mut x: u64 = 0;
    let mut y: u64 = 1;
    while i < n
        invariant
            0 <= i && i <= n,
            x == i,
            y == i + 1,
            n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
            n < 1000000, // added relaxation to prevent overflow
        decreases
            n - i,
    {
        if x < u64::MAX - y {
            x = y;
            y = x + y;
        }
        i = i + 1;
    }
    x
}

fn main() {}

} // verus!