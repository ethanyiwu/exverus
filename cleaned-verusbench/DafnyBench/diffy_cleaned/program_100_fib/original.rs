use vstd::prelude::*;

verus! {

spec fn fib(n: nat) -> nat {
    n * (n + 1) / 2
}

fn fib_iter(n: u64) -> (a: u128)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,
        n < 1000,
        n * (n + 1) / 2 < u64::MAX as u128,
    ensures
        a == n * (n + 1) / 2,
{
    let mut a: u128 = 0;
    let mut b = 1;
    let mut x = 0;
    while x < n {
        a = b;
        if b < u128::MAX - a {
            b = b + a;
        }
        x = x + 1;
    }
    a
}


}
