use vstd::prelude::*;

verus! {

// This function adds y to x, but only if y is non-negative.
// It uses a while loop to do the addition.
fn add_by_one(x: u32, y: u32) -> (r: u32)
    requires
        y >= 0,
        x + y < u32::MAX + 1,  // added requires clause to prevent overflow

    ensures
        r == x + y,
{
    x + y
}

pub fn main() {
}

} // verus!
