use vstd::prelude::*;

verus! {

/// Adds two natural numbers by incrementing the first number.
fn add_by_inc(x: u64, y: u64) -> (z: u128)  // changed return type to u128
    requires
        x < u64::MAX / 2,  // added relaxation to prevent overflow
        y < u64::MAX / 2,  // added relaxation to prevent overflow

    ensures
        z == x + y,
{
    let mut z = x as u128;  // changed type to u128
    let mut i = 0;
    while i < y {
        if z < u128::MAX - 1 {  // added check to prevent overflow
            z = z + 1;
        }
        i = i + 1;
    }
    z
}

fn main() {
}

} // verus!
