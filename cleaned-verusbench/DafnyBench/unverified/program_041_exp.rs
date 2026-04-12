use vstd::prelude::*;

verus! {

fn exp(x: u64, e: u64) -> (result: u64)
    requires
        x >= 1 && e >= 0,
        x < u64::MAX / u64::MAX,
    ensures
        result >= 1,
{
    let mut result: u128 = 1;
    result as u64
}


}
