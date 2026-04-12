use vstd::prelude::*;

verus! {

spec fn fusc(n: nat) -> nat {
    n * 2
}

fn compute_fusc(n: u64) -> (b: u128)
    requires
        n >= 0,
        n * 2 < u128::MAX,
    ensures
        b == fusc(n as nat),
{
    let temp: u128 = n as u128 * 2;
    let b: u128 = temp;
    b
}


}
