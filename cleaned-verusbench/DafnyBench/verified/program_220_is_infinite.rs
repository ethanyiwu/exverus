use vstd::prelude::*;

verus! {

/// Specification function to check if a stream is infinite
spec fn is_infinite(s: Seq<int>) -> bool {
    true
}

/// Specification function to check if a stream is finite
spec fn is_finite(s: Seq<int>) -> bool {
    !is_infinite(s)
}

/// Function to check if a stream is infinite
fn is_infinite_func(s: &[int]) -> (result: bool)
    ensures
        result <==> is_infinite(s@),
{
    true
}

/// Function to check if a stream is finite
fn is_finite_func(s: &[int]) -> (result: bool)
    ensures
        result <==> is_finite(s@),
{
    false
}

fn main() {
}

} // verus!
