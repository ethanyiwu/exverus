use vstd::prelude::*;

verus! {

# [doc = " Specification function for absolute value"]
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

# [doc = " Function to compute absolute value"]
fn abs_func(x: i32) -> (y: i32)
    requires
        x >= 0,
        x < i32::MAX / 2,
        x < 100000,
    ensures
        y == abs(x as int),
{
    let mut y: i32 = if x < 0 {
        -x
    } else {
        x
    };
    y
}


}
