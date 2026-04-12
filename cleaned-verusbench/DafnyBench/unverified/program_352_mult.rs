use vstd::prelude::*;

verus! {

fn mult(a: u32, b: u32) -> (x: u32)
    requires
        a as int >= 0,
        b as int >= 0,
        a < 1000000,
        b < 1000000,
        a * b < u32::MAX,
    ensures
        x as int == a as int * b as int,
{
    a * b
}


}
