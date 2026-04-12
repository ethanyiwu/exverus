use vstd::prelude::*;

verus! {

spec fn bool_property(b: bool) -> bool {
    b || !b
}

fn m()
    ensures
        (forall|b: bool| bool_property(b)) || 2 != 2,
{
    n();
    n();
}


}
