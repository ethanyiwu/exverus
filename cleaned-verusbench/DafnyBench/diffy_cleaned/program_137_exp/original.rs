use vstd::prelude::*;

verus! {

pub fn exp(x: u64, e: u64) -> (result: u64)
    requires
        x >= 1,
        e >= 1,
        x < u64::MAX / u64::MAX,
    ensures
        result >= 1,
{
    let mut result: u64 = 1;
    for i in 0..e {
        result = result * x;
    }
    result
}


}
