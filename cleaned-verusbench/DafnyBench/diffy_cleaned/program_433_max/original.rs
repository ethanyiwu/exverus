use vstd::prelude::*;

verus! {

spec fn max(x: nat, y: nat) -> nat {
    if x < y {
        y
    } else {
        x
    }
}

fn slow_max(a: u64, b: u64) -> (z: u64)
    ensures
        z == max(a as nat, b as nat),
{
    let mut z: u64 = 0;
    let mut x: u64 = a;
    let mut y: u64 = b;
    while z < x && z < y {
        z = z + 1;
        x = x - 1;
        y = y - 1;
    }
    if x <= y {
        b
    } else {
        a
    }
}


}
