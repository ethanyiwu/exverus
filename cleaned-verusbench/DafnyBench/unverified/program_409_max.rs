use vstd::prelude::*;
use vstd::*;

verus! {

spec fn max(a: int, b: int) -> int {
    if a > b {
        a
    } else {
        b
    }
}

fn max_func(a: int, b: int) -> (m: int)
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

spec fn post_max(a: int, b: int, m: int) -> bool {
    &&& m >= a
    &&& m >= b
    &&& (m == a || m == b)
}


}
