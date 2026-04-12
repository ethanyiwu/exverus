use vstd::prelude::*;

verus! {

fn random(a: u64, b: u64) -> (r: u64)
    requires
        a <= b,
    ensures
        a <= b ==> a <= r && r <= b,
{
    a
}


}
