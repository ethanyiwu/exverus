use vstd::prelude::*;

verus! {

pub fn eval(x: u64) -> (r: u64)
    requires
        x >= 0,
        x < 100000,
        x * x < u64::MAX,
    ensures
        r == x * x,
{
    let mut y: u64 = x;
    let mut z: u64 = x * x;
    while y > 0 && y < u64::MAX - 1 {
        y = y - 1;
    }
    return z;
}


}
