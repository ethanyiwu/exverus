use vstd::prelude::*;

verus! {

fn add_by_one(x: i32, y: u32) -> (r: i64)
    requires
        y >= 0 as u32,
        x >= i32::MIN as i64,
        x + y as i64 <= i64::MAX,
    ensures
        r == x + y as i64,
{
    let mut r: i64 = x as i64;
    let mut i: u32 = 0;
    while i < y {
        r = r + 1;
        i = i + 1;
    }
    r
}


}
