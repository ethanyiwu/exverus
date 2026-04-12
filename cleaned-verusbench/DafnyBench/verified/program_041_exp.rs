use vstd::prelude::*;

verus! {

fn exp(x: u64, e: u64) -> (result: u64)
    requires
        x >= 1 && e >= 0,
        x < u64::MAX / u64::MAX,
    ensures
        result >= 1,
{
    let mut result: u128 = 1;
    for _ in 0..e
        invariant
            result >= 1,
            x >= 1,
            e >= 0,
            x < u64::MAX / u64::MAX,
        decreases e,
    {
        if result < u64::MAX as u128 / x as u128 {
            result = result * x as u128;
        } else {
            assert(false);
        }
    }
    assert(result <= u64::MAX as u128);
    result as u64
}

fn main() {
}

} // verus!
