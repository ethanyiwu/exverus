use vstd::prelude::*;

verus! {

spec fn p() -> bool {
    false
}

fn m()
    requires
        false,
{
    n();
    assert(false);
}

fn n()
    requires
        false,
    ensures
        p(),
{
    assert(false);
}

fn main() {
}

} // verus!
