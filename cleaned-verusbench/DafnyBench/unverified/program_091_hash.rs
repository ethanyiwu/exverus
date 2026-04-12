use vstd::prelude::*;

verus! {

pub fn hash(key: u64) -> (result: u64)
    requires
        key >= 0,
    ensures
        result >= 0,
{
    key
}


}
