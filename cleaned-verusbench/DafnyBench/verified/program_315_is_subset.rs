use vstd::prelude::*;

verus! {

/// Specification function for subset
pub open spec fn is_subset(a: Seq<int>, b: Seq<int>) -> bool {
    forall|x: int| a.contains(x) ==> b.contains(x)
}

/// Specification function for subset transitivity
pub open spec fn subset_transitivity(a: Seq<int>, b: Seq<int>, c: Seq<int>) -> bool {
    is_subset(a, b) && is_subset(b, c) ==> is_subset(a, c)
}

/// Proof function for subset transitivity
proof fn subset_transitivity_proof(a: Seq<int>, b: Seq<int>, c: Seq<int>)
    requires
        is_subset(a, b),
        is_subset(b, c),
    ensures
        is_subset(a, c),
{
    assert(forall|x: int| a.contains(x) ==> c.contains(x)) by {
        assert(forall|x: int| a.contains(x) ==> b.contains(x));
        assert(forall|x: int| b.contains(x) ==> c.contains(x));
        assert(forall|x: int| a.contains(x) ==> c.contains(x));
    }
    assert(is_subset(a, c));
}

fn main() {
}

} // verus!
