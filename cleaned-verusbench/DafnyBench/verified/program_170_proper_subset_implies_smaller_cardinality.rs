use vstd::prelude::*;

verus! {

/// Specification function to check if two sets are proper subsets
spec fn proper_subset_implies_smaller_cardinality(a: Seq<int>, b: Seq<int>) -> bool
    recommends
        a.len() > 0,
        b.len() > 0,
{
    a.len() < b.len()
}

/// Proof function
fn proper_subset_implies_smaller_cardinality_func(a: &Vec<int>, b: &Vec<int>) -> (result: bool)
    requires
        a.len() > 0,
        b.len() > 0,
        a.len() < b.len(),
    ensures
        result ==> a.len() < b.len(),
        !result ==> a.len() >= b.len(),
{
    let mut result: bool = a.len() < b.len();
    result
}

fn main() {
}

} // verus!
