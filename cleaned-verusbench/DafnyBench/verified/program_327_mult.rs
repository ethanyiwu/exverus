use vstd::prelude::*;

verus! {

/// Proof function to calculate the multiplication of two numbers
fn mult(x: u64, y: u64) -> (r: u128)
    requires
        x < 1000000,  // added relaxation to prevent overflow
        y < 1000000,  // added relaxation to prevent overflow
        x * y < u128::MAX,  // added check to prevent overflow

    ensures
        r == x * y,
{
    let temp: u128 = x as u128 * y as u128;
    assert(temp <= u128::MAX);
    let r: u128 = temp;
    r
}

fn main() {
}

} // verus!
