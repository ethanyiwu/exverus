use vstd::prelude::*;

verus! {

# [doc = " Proof function to calculate the multiplication of two numbers"]
fn mult(x: u64, y: u64) -> (r: u128)
    requires
        x < 1000000,
        y < 1000000,
        x * y < u128::MAX,
    ensures
        r == x * y,
{
    let temp: u128 = x as u128 * y as u128;
    let r: u128 = temp;
    r
}


}
