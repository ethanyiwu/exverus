use vstd::prelude::*;

verus! {

fn theorem_progress(t: int) -> (result: bool)
    requires
        t >= 0,
        t < 100000,
    ensures
        result == true,
{
    true
}


}
