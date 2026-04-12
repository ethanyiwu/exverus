use vstd::prelude::*;

verus! {

/// Function to convert a set to a sequence
fn set_to_seq<T: Copy + Eq + Ord>(s: Vec<T>) -> (xs: Vec<T>)
    requires
        s.len() > 0,
    ensures
        s.len() == xs.len(),
{
    let mut left = s;
    let mut xs = Vec::new();
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

fn main() {
}

} // verus!
