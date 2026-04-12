use vstd::prelude::*;

verus! {

spec fn refinement(tr: Seq<int>) -> bool {
    true
}

fn refinement_proof(tr: Seq<int>) -> (r: bool)
    requires
        true,
    ensures
        r ==> refinement(tr),
{
    let mut r: bool = true;
    r
}


}
