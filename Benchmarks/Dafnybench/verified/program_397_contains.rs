use vstd::prelude::*;

verus! {

// Specification for what it means to check if a sequence contains an element
pub open spec fn contains(s: Seq<int>, k: int) -> bool {
    exists|i: int| 0 <= i && i < s.len() && s[i] == k
}

// Function to check if a sequence contains an element
fn contains_k(s: &[int], k: int) -> (result: bool)
    requires
        true,
    ensures
        result == contains(s@, k),
{
    let mut result = false;
    for i in 0..s.len()
        invariant
            (!result) == (!exists|j: int| 0 <= j && j < i && s[j] == k),
    {
        if s[i] == k {
            result = true;
        }
    }
    result
}

// Specification for type safety
spec fn is_type_safe(t: int) -> bool {
    // This is a placeholder for the actual type safety specification
    true
}

// Function to check type safety
fn is_type_safe_exec(t: int) -> (result: bool)
    requires
        true,
    ensures
        result == is_type_safe(t),
{
    true
}

fn main() {
}

} // verus!
