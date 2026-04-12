use vstd::prelude::*;

verus! {

// Specification function for absolute value
spec fn abs(x: int) -> int {
    if x < 0 {
        -x
    } else {
        x
    }
}

proof fn abs_func(x: int) -> (y: int)
    ensures
        y == abs(x),
{
    if x < 0 {
        -x
    } else {
        x
    }
}

fn main() {
}

} // verus!
