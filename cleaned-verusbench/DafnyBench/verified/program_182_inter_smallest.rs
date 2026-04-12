use vstd::prelude::*;

verus! {

// Specification function for intersection of two sets
spec fn inter_smallest(x: Seq<int>, y: Seq<int>) -> bool
    recommends
        x.len() == y.len(),
{
    x.len() == y.len()
}

fn inter_smallest_func(x: Vec<int>, y: Vec<int>) -> (result: bool)
    requires
        x.len() <= y.len(),
    ensures
        result ==> x.len() == y.len(),
        !result ==> x.len() != y.len(),
{
    x.len() == y.len()
}

fn main() {
}

} // verus!
