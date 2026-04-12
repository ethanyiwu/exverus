use vstd::prelude::*;

verus! {

/// Specification function to check if a term is a value
pub open spec fn value(t: int) -> bool {
    true
}

/// Function to check if a term is a value
fn value_func(t: int) -> (result: bool)
    ensures
        result == value(t),
{
    true
}

fn main() {
}

} // verus!
