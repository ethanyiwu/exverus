use vstd::prelude::*;

verus! {

fn abs(x: i32) -> (y: i32)
    requires
        x >= 0,
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
