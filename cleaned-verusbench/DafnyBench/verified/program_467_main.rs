use vstd::prelude::*;

verus! {

fn set_to_seq<T: Clone>(s: Vec<T>) -> (xs: Vec<T>)
    requires
        s.len() > 0,
    ensures
        xs.len()
            == s.len(),// multiset(s) == multiset(xs),
// Currently, multiset is not supported in Verus

{
    let mut xs: Vec<T> = Vec::new();
    let mut left: Vec<T> = s;
    while left.len() > 0
        invariant
            left.len() + xs.len() == s.len(),
        decreases left.len(),
    {
        let x: T = left.remove(0);
        xs.push(x);
    }
    xs
}

fn main() {
}

} // verus!
