use vstd::prelude::*;

verus! {

/// Specification function for a boolean property
spec fn bool_property(b: bool) -> bool {
    b || !b
}

/// Function M
fn m()
    ensures
        bool_property(true) || 2 != 2,
        bool_property(true) || 3 != 3,
        bool_property(true) || 1 != 1,
{
    n();
    assert(bool_property(true) || 0 != 0);
    n();
    assert(bool_property(true) || 3 != 3);
    assert(bool_property(true) || 1 != 1);
}

/// Function N
fn n()
    ensures
        bool_property(true) || 2 != 2,
{
    assert(bool_property(true) || 2 != 2);
}

fn main() {
}

} // verus!
