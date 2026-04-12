use vstd::prelude::*;

verus! {

spec fn max(x: int, y: int) -> int {
    if x >= y {
        x
    } else {
        y
    }
}

fn max_func(x: int, y: int) -> (r: int)
    requires
        x >= 0,
        y >= 0,
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
