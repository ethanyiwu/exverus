use vstd::prelude::*;

verus! {

// Specification function for multiplication
pub open spec fn mult(x: nat, y: nat) -> nat {
    x * y
}

// Function to multiply two numbers
fn mult_func(x: u64, y: u64) -> (r: u64)
    requires
        x > 0 && y > 0,
        x * y < u64::MAX,
    ensures
        r == mult(x as nat, y as nat),
{
    assert(x * y < u64::MAX);
    let r: u64 = x * y;
    r
}

fn main() {
}

} // verus!
