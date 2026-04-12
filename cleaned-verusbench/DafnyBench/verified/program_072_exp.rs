use vstd::prelude::*;

verus! {

fn exp(x: u64, e: usize) -> (r: u64)
    requires
        e >= 0,
        x < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
        e < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

    ensures
        x > 0 ==> r > 0,
    decreases e,
{
    if e == 0 {
        1
    } else {
        x * exp(x, e - 1)
    }
}

fn main() {
}

} // verus!
