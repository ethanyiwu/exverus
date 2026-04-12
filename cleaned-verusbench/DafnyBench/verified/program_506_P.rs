use vstd::prelude::*;

verus! {

spec fn P(x: int) -> bool;

spec fn Q(x: int) -> bool;

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
