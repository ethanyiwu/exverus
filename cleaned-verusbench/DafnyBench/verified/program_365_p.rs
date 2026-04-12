use vstd::prelude::*;

verus! {

// Specification function
spec fn p(x: int) -> bool {
    true
}

// Specification function
spec fn q(x: int) -> bool {
    true
}

// Proof function
fn test()
    requires
        forall|x: int| p(x) && q(x),
    ensures
        q(0),
{
    assert(p(0));
}

fn main() {
}

} // verus!
