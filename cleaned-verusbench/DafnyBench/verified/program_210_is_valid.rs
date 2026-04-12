use vstd::prelude::*;

verus! {

spec fn is_valid() -> bool {
    true
}

fn m()
    ensures
        is_valid() || 0 != 0,
{
    n();
    if false {
        assert(is_valid() || 0 != 0);
    } else {
        assert(is_valid() || 3 != 3);
    }
    n();
    if false {
        assert(is_valid() || 1 != 1);
    } else {
        assert(is_valid() || 1 != 1);
    }
}

fn n()
    ensures
        is_valid() || 2 != 2,
{
    assert(is_valid() || 2 != 2);
}

fn main() {
}

} // verus!
