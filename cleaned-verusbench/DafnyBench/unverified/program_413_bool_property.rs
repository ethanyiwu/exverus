use vstd::prelude::*;

verus! {

# [doc = " Specification function for a boolean property"]
spec fn bool_property(b: bool) -> bool {
    b || !b
}

# [doc = " Function M"]
fn m()
    ensures
        bool_property(true) || 2 != 2,
        bool_property(true) || 3 != 3,
        bool_property(true) || 1 != 1,
{
    n();
    n();
}


}
