use vstd::prelude::*;

verus! {

pub fn exp(x: u64, e: u64) -> (result: u64)
    requires
        x > 0,
        e > 0,
        x < u64::MAX / u64::MAX,
        x * x < u64::MAX / u64::MAX,
    ensures
        result == x * x,
{
    let mut result = x;
    for _ in 0..e {
        result = result * x;
    }
    result
}


}
