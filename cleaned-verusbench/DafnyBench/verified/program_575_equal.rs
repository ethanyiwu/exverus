use vstd::prelude::*;

verus! {

// Specification function to check if two numbers are equal
spec fn equal(x: int, y: int) -> bool {
    x == y
}

// Function to check if two numbers are equal
fn equal_func(x: int, y: int) -> (result: bool)
    ensures
        result <==> equal(x, y),
{
    x == y
}

fn main() {
}

} // verus!
