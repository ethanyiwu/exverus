use vstd::prelude::*;

verus! {

spec fn is_true(b: bool) -> bool {
    b || !b
}

fn m() {
    n();
    assert(is_true(true) || 0 != 0);
    n();
    assert(is_true(true) || 3 != 3);
    assert(is_true(true) || 1 != 1);
}

fn n() -> (ok: bool)
    ensures
        is_true(true) || 2 != 2,
{
    true
}

fn main() {
}

} // verus!
