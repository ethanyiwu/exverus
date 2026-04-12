use vstd::prelude::*;

verus! {

fn add_by_inc(x: u64, y: u64) -> (z: u128)
    requires
        x < u64::MAX / u64::MAX,
        y < u64::MAX / u64::MAX,
    ensures
        z == x as u128 + y as u128,
{
    let mut i: u64 = 0;
    let mut z: u128 = x as u128;
    while i < y {
        z = z + 1;
        i = i + 1;
    }
    z
}


}
