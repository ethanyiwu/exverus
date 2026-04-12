use vstd::prelude::*;

verus! {

fn f(x: int, y: int) -> (result: int)
    requires
        x >= 0,
        y >= 0,
        x < u64::MAX / u64::MAX,
        y < u64::MAX / u64::MAX,
        x * y < u64::MAX,
    ensures
        result == x * y,
{
    x * y
}


}
