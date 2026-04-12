use vstd::prelude::*;

verus! {

// Define a function to calculate the sum of two integers
fn sum(x: int, y: int) -> (result: int)
    ensures
        result == x + y,
{
    x + y
}

fn main() {
}

} // verus!
