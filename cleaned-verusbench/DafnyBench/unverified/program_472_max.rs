use vstd::prelude::*;

verus! {

# [doc = " Specification function for finding the maximum of two numbers"]
spec fn max(a: int, b: int) -> int {
    if a > b {
        a
    } else {
        b
    }
}

# [doc = " Function to find maximum of two numbers"]
fn max_func(a: int, b: int) -> (c: int)
    requires
        a >= 0,
        b >= 0,
    ensures
        a <= c && b <= c,
        a == c || b == c,
{
    if a > b {
        a
    } else {
        b
    }
}


}
