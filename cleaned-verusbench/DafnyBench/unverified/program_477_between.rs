use vstd::prelude::*;

verus! {

spec fn between(start: nat, i: nat, end: nat) -> bool {
    if start < end {
        start < i && i < end
    } else {
        i < end || start < i
    }
}

fn max(a: int, b: int) -> (max: int)
    requires
        true,
    ensures
        max >= a && max >= b,
        max == a || max == b,
{
    if a > b {
        return a;
    } else {
        return b;
    }
}


}
