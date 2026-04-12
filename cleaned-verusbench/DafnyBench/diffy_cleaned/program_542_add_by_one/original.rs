use vstd::prelude::*;

verus! {

# [doc = " Function to add two numbers by incrementing the first number by one until the second number is zero."]
fn add_by_one(x: i32, y: u32) -> (r: i64)
    requires
        y >= 0,
        x >= i32::MIN,
        x <= i32::MAX,
        y < i32::MAX as u32,
        x + y as i32 >= i64::MIN,
        x + y as i32 <= i64::MAX,
    ensures
        r == x as i64 + y as i64,
{
    let mut i: u32 = 0;
    let mut r: i64 = x as i64;
    while i < y {
        r = r + 1;
        i = i + 1;
    }
    r
}


}
