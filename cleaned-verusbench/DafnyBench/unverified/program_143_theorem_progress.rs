use vstd::prelude::*;

verus! {

fn theorem_progress(t: &[u8]) -> (result: bool)
    requires
        true,
    ensures
        result == true,
{
    true
}


}
