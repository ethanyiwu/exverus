use vstd::prelude::*;

verus! {

# [doc = " Specification function for maximum"]
spec fn max(x: int, y: int) -> int {
    if x >= y {
        x
    } else {
        y
    }
}

# [doc = " Function to find maximum of two numbers"]
fn max_func(x: int, y: int) -> (r: int)
    requires
        x >= 0,
        y >= 0,
    ensures
        r >= x && r >= y,
        r == x || r == y,
{
    if x >= y {
        x
    } else {
        y
    }
}


}
