use vstd::prelude::*;

verus! {

pub fn ninety_one(x: i32) -> (z: i32)
    requires
        x >= 91 && x <= 101,
    ensures
        z == if x > 101 {
            x - 10
        } else {
            91
        },
{
    if x > 101 {
        return x - 10;
    } else {
        return 91;
    }
}

pub fn gcd(x1: u64, x2: u64) -> (result: u64)
    requires
        1 <= x1 && 1 <= x2,
    ensures
        result != 0,
{
    let mut y1: u64 = x1;
    let mut y2: u64 = x2;
    while y1 != y2 && y1 > y2 {
        y1 = y1 - y2;
    }
    let mut y3: u64 = y2;
    let mut y4: u64 = y1;
    while y3 != y4 && y3 > y4 {
        y3 = y3 - y4;
    }
    y3
}


}
