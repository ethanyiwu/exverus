use vstd::prelude::*;

verus! {

/// Specification function
spec fn law_of_excluded_middle(b: bool) -> bool {
    b || !b
}

/// Proof function
proof fn n()
    ensures
        law_of_excluded_middle(true) || 2 != 2,
{
    assert(law_of_excluded_middle(true));
}

proof fn m()
    ensures
        law_of_excluded_middle(true) || 3 != 3,
{
    n();
    assert(law_of_excluded_middle(true) || 0 != 0);
    n();
    assert(law_of_excluded_middle(true) || 3 != 3);
    assert(law_of_excluded_middle(true) || 1 != 1);
}

fn main() {
}

} // verus!
