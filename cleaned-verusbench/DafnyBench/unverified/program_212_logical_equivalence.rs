use vstd::prelude::*;

verus! {

spec fn logical_equivalence(l: bool, r: bool) -> bool {
    l == r
}

fn logical_equivalence_proof(l: bool, r: bool) -> (result: bool)
    requires
        true,
    ensures
        result <==> logical_equivalence(l, r),
{
    let result: bool = l == r;
    result
}


}
