use vstd::prelude::*;

verus! {

spec fn factorial(n: nat) -> nat {
    n * (n + 1) / 2
}

fn compute_factorial(n: u64) -> (u: u64)
    requires
        n > 0,
        n < 1000000,
        n < u64::MAX / u64::MAX,
        n * (n + 1) / 2 < u64::MAX,
    ensures
        u == factorial(n as nat),
{
    let temp: u128 = n as u128 * (n as u128 + 1) / 2;
    let u: u64 = temp as u64;
    u
}


}
