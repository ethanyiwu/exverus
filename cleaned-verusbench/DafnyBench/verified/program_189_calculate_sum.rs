use vstd::prelude::*;

verus! {

// Define a function to calculate the sum of two numbers
fn calculate_sum(a: int, b: int) -> (result: int)
    ensures
        result == a + b,
{
    a + b
}

fn main() {
}

} // verus!
