use vstd::prelude::*;

verus! {

// Define a function to calculate the sum of two integers
fn add(a: int, b: int) -> (result: int)
    ensures
        result == a + b,
{
    a + b
}

fn main() {
}

} // verus!
