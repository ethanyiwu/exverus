use vstd::prelude::*;

verus! {

fn add(a: u32, b: u32) -> (result: u32)
    requires
        a >= 0,
        b >= 0,
        a + b < u32::MAX,
    ensures
        result == a + b,
{
    a + b
}


}
