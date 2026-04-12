use vstd::prelude::*;

verus! {

fn add_by_one(x: u32, y: u32) -> (r: u64)
    requires
        x >= 0,
        y >= 0,
        x < u64::MAX / 2,
        y < u64::MAX - x,
    ensures
        r == x + y,
{
    let mut i: u32 = 0;
    let mut r: u64 = x as u64;
    while i < y {
        if r < u64::MAX - 1 {
            r = r + 1;
        }
        i = i + 1;
    }
    r
}


}
