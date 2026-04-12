use vstd::prelude::*;

verus! {

pub fn my_sqrt(x: u32) -> (res: u32)
    ensures
        res * res <= x < (res + 1) * (res + 1),
{
    if x == 0 {
        return 0
    }
    if (x == 1 || x == 2) {
        return 1
    }
    let mut bg = 1;
    let mut ed = x - 1;
    let mut mid;
    while ed > bg + 1 {
        mid = bg + (ed - bg) / 2;
        let tmp = x / mid;
        if tmp == mid {
            return mid;
        }
        if tmp > mid {
            bg = mid;
        } else {
            ed = mid;
        }
    }

    return bg;
}

} // verus!
fn main() {}
