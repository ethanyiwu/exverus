use vstd::prelude::*;

fn main() {}
verus! {

fn cal_div() -> (r: (u32, u32))
    ensures
        r.0 == 27,
        r.1 == 2,
{
    let mut x: u32 = 0;
    let mut y: u32 = 191;
    let mut cnt: u32 = 0;
    while y > 6 {
        x = x + 1;
        y = 191 - 7 * x;
        cnt = x;
    }
    (x, y)
}

} // verus!
