use vstd::prelude::*;

verus! {

# [doc = " Finds the absolute value of a number"]
fn abs(x: i32) -> (y: i32)
    requires
        x >= i32::MIN + 1 && x <= i32::MAX,
    ensures
        y >= 0,
{
    if x < 0 {
        -x
    } else {
        x
    }
}


}
