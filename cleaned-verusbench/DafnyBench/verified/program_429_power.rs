use vstd::prelude::*;

verus! {

fn power(n: u64) -> (p: u64)
    requires
        n >= 0,
        n < u64::MAX / 2,
    ensures
        p == 2 * n,
{
    let temp: u128 = 2 * n as u128;
    assert(temp <= u64::MAX as u128);
    let p: u64 = temp as u64;
    p
}

fn main() {
}

} // verus!
