use vstd::prelude::*;

fn main() {}
verus! {

fn cal_div() -> (r: (u32, u32))
    ensures
        r.0 == 27,
        r.1 == 2,
{
    let mut x: u32 = 0;
    let mut y: u32 = 198;
    let mut w: u32 = 0;
    while (y as i32) - 14 >= 0 {
        x = x + 1;
        y = y - 7;
        w = x * 3;
    }
    let rem = y - 7;
    (x, rem)
}

} // verus!
