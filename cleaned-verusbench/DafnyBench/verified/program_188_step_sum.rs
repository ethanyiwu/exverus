use vstd::prelude::*;

verus! {

fn step_sum(xs: Vec<usize>) -> (sum: usize)
    requires
        xs.len() > 0,
        xs.len() < 100,
    ensures
        sum == xs.len(),
{
    xs.len()
}

fn main() {
}

} // verus!
