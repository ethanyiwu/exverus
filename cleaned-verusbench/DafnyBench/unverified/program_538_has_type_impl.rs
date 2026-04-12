use vstd::prelude::*;

verus! {

spec fn has_type_impl(t: int) -> bool
    recommends
        true,
{
    true
}

fn has_type(t: int) -> (r: bool)
    ensures
        r == has_type_impl(t),
{
    true
}


}
