use vstd::prelude::*;

verus! {

fn non_zero_return(x: i32) -> (y: i32)
    requires
        x <= i32::MAX && x >= i32::MIN + 1,
        x == 0 ==> x + 1 <= i32::MAX,
        x != 0 ==> -x >= i32::MIN,
    ensures
        y != 0,
{
    if x == 0 {
        x + 1
    } else {
        -x
    }
}


}
