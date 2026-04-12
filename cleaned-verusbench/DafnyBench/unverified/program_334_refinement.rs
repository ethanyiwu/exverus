use vstd::prelude::*;

verus! {

fn refinement(tr: &[int]) -> (result: bool)
    requires
        tr.len() > 0,
        tr.len() <= i32::MAX as usize,
    ensures
        true,
{
    true
}


}
