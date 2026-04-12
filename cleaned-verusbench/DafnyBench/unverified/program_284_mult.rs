use vstd::prelude::*;

verus! {

fn mult(a: u32, b: u32) -> (x: u32)
    requires
        a as int >= 0,
        b as int >= 0,
        a < 1000,
        b < 1000,
        a as int * b as int >= 0,
        a as int * b as int <= u32::MAX as int,
    ensures
        x as int == a as int * b as int,
{
    let temp: u128 = a as u128 * b as u128;
    let x: u32 = temp as u32;
    x
}


}
