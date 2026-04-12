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
    let mut z: u32 = x ^ y;
    while (y + 1) > 7
        invariant
            7 * x + y == 191,
        decreases y,
    {
        x = x + 1;
        y = 191 - 7 * x;
        z = x ^ y;
    }
    (x, y)
}

} // verus!
