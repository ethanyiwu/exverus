use vstd::prelude::*;

verus! {

/// Function to convert a set to a sequence
fn set_to_seq<T: Copy>(s: &Vec<T>) -> (xs: Vec<T>)
    requires
        s.len() > 0,
    ensures
        xs.len() == s.len(),
{
    let mut xs: Vec<T> = Vec::new();
    let mut left: Vec<T> = s.clone();
    while left.len() > 0
        invariant
            left.len() + xs.len() == s.len(),
        decreases left.len(),
    {
        let x = left.remove(0);
        xs.push(x);
    }
    xs
}

fn main() {}
} // verus!