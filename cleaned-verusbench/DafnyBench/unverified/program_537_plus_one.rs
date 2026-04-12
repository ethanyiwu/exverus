use vstd::prelude::*;

verus! {

# [doc = " Function to add one to a number"]
fn plus_one(x: u64) -> (y: u64)
    requires
        x >= 0,
        x < u64::MAX,
        x > 0,
    ensures
        y > 0,
{
    let y: u64 = x + 1;
    y
}


}
