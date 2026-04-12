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
    n();
}


}
