use vstd::prelude::*;

verus! {

fn abs(x: i32) -> (y: i32)
    requires
        x >= 0,
    ensures
        y == x,
{
    x
}


}
