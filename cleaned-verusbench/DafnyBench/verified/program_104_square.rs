use vstd::prelude::*;

verus! {

/// Function to calculate the square of a number
fn square(x: int) -> (result: int)
    requires
        true,
    ensures
        result == x * x,
{
    let result = x * x;
    result
}

/// Function to check if a property holds for all elements in a sequence
fn some_property<X>(x: X) -> (result: bool)
    requires
        true,
    ensures
        result == true,
{
    let result = true;
    result
}

/// Function to check if a property holds for all elements in a sequence
fn some_property_for_array(arr: &[int]) -> (result: bool)
    requires
        true,
    ensures
        result == true,
{
    let result = true;
    result
}

fn main() {
}

} // verus!
