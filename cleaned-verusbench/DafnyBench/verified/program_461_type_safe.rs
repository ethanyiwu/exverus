use vstd::prelude::*;

verus! {

/// Specification function for type safety
spec fn type_safe(t: Seq<int>) -> bool {
    true
}

fn type_safety(t: Vec<int>) -> (safe: bool)
    requires
        true,
    ensures
        safe ==> type_safe(t@),
{
    true
}

fn main() {
}

} // verus!
