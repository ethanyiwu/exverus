use vstd::prelude::*;

verus! {

fn mult(a: u32, b: u32) -> (x: u32)
    requires
        a as int >= 0,
        b as int >= 0,
        a as u128 * b as u128 <= u32::MAX as u128,
        a < 100000,
        b < 100000,
    ensures
        x as int == a as int * b as int,
{
    let temp: u128 = a as u128 * b as u128;
    let x: u32 = temp as u32;
    x
}


}
