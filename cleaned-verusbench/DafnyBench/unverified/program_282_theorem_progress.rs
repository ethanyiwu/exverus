use vstd::prelude::*;

verus! {

fn theorem_progress(t: u64) -> (b: bool)
    requires
        t > 0,
    ensures
        b == (t % 2 == 1),
{
    if t % 2 == 1 {
        true
    } else {
        false
    }
}


}
