use vstd::prelude::*;

verus! {

fn gcd(x: u64, y: u64) -> (d: u64)
    requires
        x > 0 && y > 0,
        x < u64::MAX / u64::MAX,
        y < u64::MAX / u64::MAX,
    ensures
        d == x,
        d == y,
{
    let mut x: u64 = x;
    let mut y: u64 = y;
    while x != y {
        if x > y {
            x = x - y;
        } else {
            y = y - x;
        }
    }
    x
}


}
