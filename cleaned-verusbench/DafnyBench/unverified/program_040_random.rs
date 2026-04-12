use vstd::prelude::*;

verus! {

fn random(a: u64, b: u64) -> (r: u64)
    requires
        a <= b,
    ensures
        a <= r && r <= b,
{
    let mut r: u64 = a;
    if a != b {
        r += 1;
    }
    r
}


}
