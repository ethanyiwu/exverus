use vstd::prelude::*;

verus! {

// Specification function
spec fn p() -> bool {
    false
}

// Target function
fn n()
    requires
        false,
    ensures
        p(),
{
    assert(false);
}

fn m()
    requires
        false,
    ensures
        false,
{
    n();
    assert(false);
}

fn main() {
}

} // verus!
