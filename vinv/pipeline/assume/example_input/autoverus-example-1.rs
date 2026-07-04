
use vstd::prelude::*;

verus! {

#[verifier::loop_isolation(false)]

fn cal_div() -> (r: (u32, u32))
    ensures
        r.0 == 27,
        r.1 == 2,
{
    let mut x: u32 = 0;
    let mut y: u32 = 191;
    while 7 <= y
    invariant 
        7 <= y,
        x <= 27, // Ensuring x does not exceed 27 to prevent overflow in `7 * x`
    decreases y
    {
        // Ensures no overflow for `7 * x` in `191 - 7 * x`
        assert(191 >= 7 * x); 

        // Main assertion to prevent underflow in `191 - 7 * x`
        assert(x <= 27); 

        x = x + 1;

        // Main assertion added right before `y = 191 - 7 * x;`
        assert(191 >= 7 * x); // Ensure no underflow before the assignment

        y = 191 - 7 * x; 
    }
    (x, y)
}

} // verus!

fn main() {}

// Score: (0, 2)
// Safe: True