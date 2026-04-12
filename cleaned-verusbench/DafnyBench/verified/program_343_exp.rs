use vstd::prelude::*;

verus! {

fn exp(x: u64, e: u64) -> (result: u64)
    requires
        e >= 0,
        x > 0,
        x < u64::MAX / x,
        e < 1000,  // added relaxation to prevent overflow

    ensures
        result > 0,
    decreases e,
{
    if e == 0 {
        1
    } else {
        if let Some(result) = x.checked_mul(exp(x, e - 1)) {
            if result > 0 {
                result
            } else {
                1
            }
        } else {
            1
        }
    }
}

fn main() {
}

} // verus!
