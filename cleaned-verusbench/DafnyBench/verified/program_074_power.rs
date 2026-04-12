use vstd::prelude::*;

verus! {

fn power(a: u64, n: u64) -> (result: u64)
    requires
        a > 0,
        n >= 0,
        a < u64::MAX / u64::MAX,
    ensures
        result == a * n,
{
    let temp: u128 = a as u128 * n as u128;
    assert(temp <= u64::MAX as u128);
    let result: u64 = temp as u64;
    assert(result == a * n);
    result
}

fn main() {
}

} // verus!
