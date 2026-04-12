use vstd::prelude::*;

verus! {

fn add_by_one(x: i32, y: i32) -> (r: i32)
    requires
        y >= 0,
        x + y >= i32::MIN,
        x + y <= i32::MAX,
    ensures
        r == x + y,
{
    let mut i: i32 = 0;
    let mut r: i32 = x;
    while i < y {
        r = r + 1;
        i = i + 1;
    }
    r
}


}
