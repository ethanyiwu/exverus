use vstd::prelude::*;

verus! {

fn exp(x: u64, e: usize) -> (r: u64)
    requires
        e >= 0,
        x < u64::MAX / u64::MAX,
        e < u64::MAX / u64::MAX,
    ensures
        x > 0 ==> r > 0,
{
    if e == 0 {
        1
    } else {
        x * exp(x, e - 1)
    }
}


}
