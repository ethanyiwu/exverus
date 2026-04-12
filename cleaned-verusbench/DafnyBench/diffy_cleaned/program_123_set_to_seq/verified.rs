use vstd::prelude::*;

verus! {

fn set_to_seq(s: Vec<i32>) -> (xs: Vec<i32>)
    requires
        s.len() < 1000000,
    ensures
        xs.len() == s.len(),
{
    let mut xs: Vec<i32> = Vec::new();
    let mut left: Vec<i32> = s;
    while left.len() > 0
        invariant
            xs.len() + left.len() == s.len(),
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
