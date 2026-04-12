use vstd::prelude::*;

verus! {

fn q1_logical_equivalence_as_a_conjunction_of_two_implications__PROOF_BY_TRUTH_TABLE__in_a_comment(
    l: bool,
    r: bool,
) -> (result: bool)
    ensures
        (l <==> r) <==> (l ==> r) && (!l ==> !r),
{
    if l {
        if r {
            true
        } else {
            false
        }
    } else {
        if r {
            false
        } else {
            true
        }
    }
}


}
