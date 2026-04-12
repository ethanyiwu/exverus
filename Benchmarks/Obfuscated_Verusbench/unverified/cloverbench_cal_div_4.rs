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
    let mut phase: u32 = 0;
    let mut counter: u32 = 0;

    while y >= 7 {
        x = x + 1;
        y = 191 - 7 * x;
        phase = (phase + 1) % 2;
        counter = counter + 3;
    }
    (x, y)
}

} // verus!
