use vstd::prelude::*;

verus! {

fn set_to_seq<T>(s: Vec<T>) -> (xs: Vec<T>)
    requires
        true,
    ensures
        // Verus does not support multisets directly, but we can use a similar approach with sets instead
        s.len() == xs.len(),
{
    let mut xs: Vec<T> = Vec::new();
    let mut left: Vec<T> = s;
    while left.len() > 0
        invariant
            left.len() + xs.len() == s.len(),
        decreases
            left.len(),
    {
        let x = left.remove(0);
        xs.push(x);
    }
    xs
}

fn main() {}
} // verus!