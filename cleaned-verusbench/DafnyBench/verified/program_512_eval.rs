use vstd::prelude::*;

verus! {

pub fn eval(x: u64) -> (r: u64)
    requires
        x >= 0,
        x * x < u64::MAX,  // added relaxation to prevent overflow

    ensures
        r == x * x,
{
    let temp: u128 = x as u128 * x as u128;
    assert(temp <= u64::MAX as u128);
    let r: u64 = temp as u64;
    r
}

fn main() {
}

} // verus!
