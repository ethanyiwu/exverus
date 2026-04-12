use vstd::prelude::*;

verus! {

/// Specification function to check if a boolean is true or false
spec fn is_bool(b: bool) -> bool {
    b || !b
}

/// Proof function to check if a boolean is true or false
fn m() {
    n();
    if false {
        assert(is_bool(true) || 0 != 0);
    } else {
        assert(is_bool(true) || 0 != 0);
    }
    n();
    assert(is_bool(true) || 3 != 3);
    if false {
        assert(is_bool(true) || 1 != 1);
    } else {
        assert(is_bool(true) || 1 != 1);
    }
}

/// Proof function to check if a boolean is true or false
fn n()
    ensures
        is_bool(true) || 2 != 2,
{
    assert(is_bool(true) || 2 != 2);
}

fn main() {
}

} // verus!
