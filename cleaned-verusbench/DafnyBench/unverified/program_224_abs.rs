use vstd::prelude::*;

verus! {

# [doc = " Function to calculate the absolute value of a number"]
fn abs(x: int) -> (y: int)
    requires
        x >= 0,
    ensures
        y == x,
{
    x
}


}
