use vstd::prelude::*;

verus! {

struct Reg;

fn mult(x: u64, y: u64) -> (r: u64)
    requires
        x >= 0,
        y >= 0,
        x * y < u64::MAX,
    ensures
        r == x * y,
{
    x * y
}


}
