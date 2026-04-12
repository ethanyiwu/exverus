use vstd::prelude::*;

verus! {

/// Specification function
spec fn P(x: int) -> bool {
    true
}

/// Specification function
spec fn Q(x: int) -> bool {
    true
}

fn test()
    requires
        forall|x: int| #![trigger P(x)] P(x) && Q(x),
    ensures
        Q(0),
{
    assert(P(0));
}

fn main() {
}

} // verus!
