use vstd::prelude::*;

verus! {

fn max(a: int, b: int) -> (m: int)
    ensures
        m >= a,
        m >= b,
        m == a || m == b,
{
    if a > b {
        a
    } else {
        b
    }
}


}
