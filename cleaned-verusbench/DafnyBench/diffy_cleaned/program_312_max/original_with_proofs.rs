use vstd::prelude::*;

verus! {

spec fn max(x: int, y: int) -> int {
    if x < y {
        y
    } else {
        x
    }
}

fn slow_max(a: u64, b: u64) -> (z: u64)
    ensures
        z == max(a as int, b as int),
{
    let mut z: u64 = 0;
    let mut x: u64 = a;
    let mut y: u64 = b;
    while z < x && z < y
        invariant
            x >= 0,
            y >= 0,
            z == a - x,
            z == b - y,
            a - x == b - y,
        decreases x, y,
    {
        z += 1;
        x -= 1;
        y -= 1;
    }
    if x <= y {
        b
    } else {
        a
    }
}

fn main() {
}

} // verus!