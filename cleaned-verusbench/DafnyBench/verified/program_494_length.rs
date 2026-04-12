use vstd::prelude::*;

verus! {

// Define a function to calculate the length of a string
fn length(s: &[char]) -> (len: usize)
    ensures
        len == s.len(),
{
    s.len()
}

fn main() {
}

} // verus!
