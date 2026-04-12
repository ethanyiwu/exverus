use vstd::prelude::*;

verus! {

# [doc = " Specification function to find the maximum of two natural numbers"]
pub open spec fn max(x: nat, y: nat) -> nat
    recommends
        x >= 0 && y >= 0,
{
    if x >= y {
        x
    } else {
        y
    }
}

# [doc = " Function to find the maximum of two natural numbers"]
fn max_func(x: u64, y: u64) -> (r: u64)
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
