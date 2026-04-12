use vstd::prelude::*;

verus! {

// Define a function to calculate the maximum of two integers
fn max(a: int, b: int) -> (result: int)
    ensures
        result >= a,
        result >= b,
{
    if a >= b {
        a
    } else {
        b
    }
}

fn main() {
}

} // verus!
