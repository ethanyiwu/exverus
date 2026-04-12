use vstd::prelude::*;

verus! {

spec fn fib(n: nat) -> nat
    recommends
        n >= 0,
{
    n * n
}

fn compute_fib(n: u64) -> (f: u64)
    requires
        n >= 0,
        n < 1000,
        n * n < u64::MAX,
    ensures
        f == fib(n as nat),
{
    let temp: u128 = n as u128 * n as u128;
    let f: u64 = temp as u64;
    f
}


}
