use vstd::prelude::*;

verus! {

// Specification function to check if a boolean value is either true or false
spec fn bool_property(b: bool) -> bool {
    b || !b
}

// Function M
fn m()
    ensures
        (forall|b: bool| bool_property(b)) || 2 != 2,
{
    n();
    if false {
        assert(bool_property(true));
    } else {
        assert(bool_property(false)) by {
            assert(bool_property(true));
        }
        assert((forall|b: bool| bool_property(b)) || 0 != 0);
    }
    n();
    assert((forall|b: bool| bool_property(b)) || 3 != 3);
    if false {
        assert(bool_property(true));
    } else {
        assert(bool_property(false)) by {
            assert(bool_property(true));
        }
        assert((forall|b: bool| bool_property(b)) || 1 != 1);
    }
}

// Function N
fn n()
    ensures
        (forall|b: bool| bool_property(b)) || 2 != 2,
{
    assert(forall|b: bool| bool_property(b));
}

fn main() {
}

} // verus!
