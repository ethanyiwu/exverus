use vstd::prelude::*;

verus! {

fn mult(x: u64, y: u64) -> (r: u64)
    requires
        x >= 0,
        y >= 0,
        x * y < u64::MAX,
    ensures
        r == x * y,
{
    let r = x * y;
    r
}


}
