use vstd::prelude::*;

verus! {

fn max(x: int, y: int) -> (m: int)
    requires
        true,
    ensures
        m >= x && m >= y,
        (x >= y ==> m == x) && (x < y ==> m == y),
{
    if x > y {
        x
    } else {
        y
    }
}


}
