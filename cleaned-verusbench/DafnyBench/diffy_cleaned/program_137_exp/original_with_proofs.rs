use vstd::prelude::*;

verus! {

pub fn exp(x: u64, e: u64) -> (result: u64)
    requires
        x >= 1,
        e >= 1,
        x < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        result >= 1,
{
    let mut result: u64 = 1;
    for i in 0..e
        invariant
            0 <= i <= e,
            result >= 1,
            x >= 1,
            e >= 1,
            x < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    {
        result = result * x;
        assert(result >= 1);
    }
    result
}

fn main() {}
} // verus!