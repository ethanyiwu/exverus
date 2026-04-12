use vstd::prelude::*;

verus! {

fn add_by_one(x: i32, y: u32) -> (r: i32)
    requires
        y >= 0,
        y < i32::MAX as u32, // added relaxation to prevent overflow
        x < i32::MAX - y as i32, // added relaxation to prevent overflow
    ensures
        r == x + y as i32,
{
    let mut i: u32 = 0;
    let mut r: i32 = x;
    while i < y
        invariant
            i <= y,
            r == x + i as i32,
            y >= 0,
            y < i32::MAX as u32,
            x < i32::MAX - y as i32,
        decreases
            y as int - i as int,
    {
        r = r + 1;
        i = i + 1;
    }
    r
}

fn main() {}

} // verus!