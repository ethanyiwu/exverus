use vstd::prelude::*;

verus! {

spec fn fusc(n: nat) -> nat {
    n * 2
}

fn compute_fusc(n: u64) -> (b: u128)
    requires
        n >= 0,
        n * 2 < u128::MAX,  // added a check to prevent overflow

    ensures
        b == fusc(n as nat),
{
    let temp: u128 = n as u128 * 2;
    assert(temp <= u128::MAX);
    let b: u128 = temp;
    assert(b == n * 2);
    b
}

fn main() {
}

} // verus!
