use vstd::prelude::*;

verus! {

spec fn value<T: Copy>(t: T, value_t: T) -> bool {
    value_t == t
}

fn has_type<T: Copy>(t: T) -> (result: T)
    requires
        value(t, t),
    ensures
        result == t,
{
    t
}


}
