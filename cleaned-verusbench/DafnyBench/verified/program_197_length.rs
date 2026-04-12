use vstd::prelude::*;

verus! {

// Define a function to calculate the length of a string
fn length(s: &Vec<char>) -> (result: usize)
    ensures
        result >= 0,
        result == s.len(),
{
    s.len()
}

fn main() {
}

} // verus!
