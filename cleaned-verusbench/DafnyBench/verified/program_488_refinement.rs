use vstd::prelude::*;

verus! {

// Specification for refinement
spec fn refinement(tr: Seq<int>) -> bool {
    true
}

// Proof function to prove refinement
fn refinement_proof(tr: Seq<int>) -> (r: bool)
    requires
        true,
    ensures
        r ==> refinement(tr),
{
    let mut r: bool = true;
    r
}

fn main() {
}

} // verus!
