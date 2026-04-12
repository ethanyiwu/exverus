use vstd::prelude::*;

verus! {

# [doc = " Adds two natural numbers by incrementing the first number."]
fn add_by_inc(x: u64, y: u64) -> (z: u128)
    requires
        x < u64::MAX / 2,
        y < u64::MAX / 2,
    ensures
        z == x + y,
{
    let mut z = x as u128;
    let mut i = 0;
    while i < y {
        if z < u128::MAX - 1 {
            z = z + 1;
        }
        i = i + 1;
    }
    z
}


}
