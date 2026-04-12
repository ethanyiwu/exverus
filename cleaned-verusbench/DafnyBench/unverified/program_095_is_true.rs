use vstd::prelude::*;

verus! {

spec fn is_true(b: bool) -> bool {
    b || !b
}

fn m() {
    n();
    n();
}

fn n() -> (ok: bool)
    ensures
        is_true(true) || 2 != 2,
{
    true
}


}
