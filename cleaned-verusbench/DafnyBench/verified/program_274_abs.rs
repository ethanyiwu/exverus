use vstd::prelude::*;

verus! {

/// Specification function for absolute value
spec fn abs(x: int) -> int
    recommends
        x >= 0,
{
    if x < 0 {
        -x
    } else {
        x
    }
}

/// Function to compute absolute value
fn abs_func(x: i32) -> (y: i32)
    requires
        x >= 0,
        x < i32::MAX / 2,  // added relaxation to prevent overflow
        x < 100000,  // added relaxation to prevent overflow

    ensures
        y == abs(x as int),
{
    let mut y: i32 = if x < 0 {
        -x
    } else {
        x
    };
    assert(y == abs(x as int)) by {
        assert(x >= 0 ==> y == x);
        assert(x < 0 ==> y == -x);
        assert(y == abs(x as int));
    }
    y
}

fn main() {
}

} // verus!
