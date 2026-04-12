use vstd::prelude::*;

verus! {

fn add_by_one(x: u32, y: u32) -> (r: u32)
    requires
        y >= 0,
        x + y < u32::MAX + 1,
    ensures
        r == x + y,
{
    x + y
}


}
