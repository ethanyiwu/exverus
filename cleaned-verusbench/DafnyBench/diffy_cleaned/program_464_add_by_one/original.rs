use vstd::prelude::*;

verus! {

fn add_by_one(x: u32, y: u32) -> (r: u64)
    requires
        y >= 0,
    ensures
        r == (x as u64) + (y as u64),
{
    let mut i: u32 = 0;
    let mut r: u64 = x as u64;
    while i < y {
        r = r + 1;
        i = i + 1;
    }
    r
}


}
