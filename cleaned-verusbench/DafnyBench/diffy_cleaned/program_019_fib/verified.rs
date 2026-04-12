use vstd::prelude::*;

verus! {

spec fn fib(n: nat) -> nat {
    n * (n + 1) / 2
}

fn fib_iter(n: u64) -> (a: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,
    ensures
        a == n * (n + 1) / 2,
{
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    let mut x: u64 = 0;
    while x < n
        invariant
            0 <= x && x <= n,
            x == a,
            x + 1 == b,
            n > 0,
            n < u64::MAX / u64::MAX,
        decreases n - x,
    {
        a = b;
        if b < u64::MAX - a {
            b = a + b;
        }
        x = x + 1;
    }
    assert(a == n * (n + 1) / 2);
    a
}

fn main() {
}

} // verus!
