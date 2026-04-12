use vstd::prelude::*;

verus! {

fn max(x: int, y: int) -> (m: int)
    ensures
        m >= x,
        m >= y,
        m == x || m == y,
{
    if x > y {
        x
    } else {
        y
    }
}

fn main() {
}

} // verus!
