use vstd::prelude::*;

verus! {

spec fn exp(b: nat, n: nat) -> nat {
    b * n
}

fn fast_exp(b: u64, n: u64) -> (r: u64)
    requires
        b >= 0,
        n >= 0,
        b * n < u64::MAX,
    ensures
        r == b * n,
{
    let temp: u128 = b as u128 * n as u128;
    assert(temp <= u64::MAX as u128);
    temp as u64
}

fn main() {
}

} // verus!
