use vstd::prelude::*;

verus! {

pub fn gen(start: int) -> (x: int)
    requires
        true,
    ensures
        x == start,
{
    start
}


}
