use vstd::prelude::*;

verus! {

spec fn p() -> bool {
    false
}

fn m()
    requires
        false,
    ensures
        false,
{
    n();
}


}
