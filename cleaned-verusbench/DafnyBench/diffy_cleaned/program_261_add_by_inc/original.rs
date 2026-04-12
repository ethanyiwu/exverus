use vstd::prelude::*;

verus! {

fn add_by_inc(x: u64, y: u64) -> (z: u64)
    requires
        x < u64::MAX / 2,
        y < u64::MAX / 2,
    ensures
        z == x + y,
{
    let mut z = x;
    let mut i = 0;
    while i < y {
        z = z + 1;
        i = i + 1;
    }
    z
}


}
