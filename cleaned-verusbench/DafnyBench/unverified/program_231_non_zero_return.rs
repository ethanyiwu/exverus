use vstd::prelude::*;

verus! {

fn non_zero_return(x: i32) -> (y: i32)
    requires
        x != i32::MIN && x != i32::MAX,
    ensures
        y != 0,
{
    if x == 0 {
        x + 1
    } else {
        -x
    }
}

fn test() {
    let input = non_zero_return(-1);
}


}
