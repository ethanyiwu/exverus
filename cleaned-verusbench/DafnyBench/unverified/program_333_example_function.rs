use vstd::prelude::*;

verus! {

pub fn example_function(x: i32) -> (y: i32)
    requires
        x >= i32::MIN / 2 && x <= i32::MAX / 2,
    ensures
        y == x * 2,
{
    x.wrapping_mul(2)
}


}
