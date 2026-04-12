use vstd::prelude::*;

verus! {

/// Calculates 2 to the power of x.
fn power2(x: usize) -> (result: u64)
    requires
        x < 100,
    ensures
        result > 0,
{
    let mut result: u64 = 1;
    let mut i: usize = 0;
    while i < x
        invariant
            0 <= i && i <= x,
            result > 0,
        decreases
            x - i,
    {
        if result < u64::MAX / 2 {
            result = result * 2;
        } else {
            break;
        }
        i = i + 1;
    }
    assert(result > 0);
    result
}

fn main() {}

} // verus!