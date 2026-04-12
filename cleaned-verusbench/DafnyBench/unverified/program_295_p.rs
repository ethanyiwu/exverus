use vstd::prelude::*;

verus! {

spec fn p() -> bool {
    false
}

fn m()
    requires
        false,
{
    n();
}


}
