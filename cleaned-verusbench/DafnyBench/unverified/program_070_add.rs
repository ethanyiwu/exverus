use vstd::prelude::*;

verus! {

# [doc = " Specification function for addition"]
spec fn add(x: int, y: int) -> int {
    x + y
}

# [doc = " Function to add two numbers using increment"]
fn add_by_inc(x: u64, y: u64) -> (z: u64)
    requires
        x >= 0,
        y >= 0,
        x < u64::MAX / u64::MAX,
        y < u64::MAX / u64::MAX,
        x + y < u64::MAX,
    ensures
        z == x + y,
{
    let mut z: u64 = x;
    let mut i: u64 = 0;
    while i < y {
        if z < u64::MAX - 1 {
            z = z + 1;
        }
        i = i + 1;
    }
    z
}


}
