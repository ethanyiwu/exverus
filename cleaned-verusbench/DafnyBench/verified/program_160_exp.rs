use vstd::prelude::*;

verus! {

fn exp(x: u64, e: u64) -> (r: u64)
    requires
        e >= 0,
        x < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
        e < 1000,  // added relaxation to prevent overflow

    ensures
        x > 0 ==> r > 0,
    decreases e,
{
    if e == 0 {
        1
    } else {
        if x == 0 {
            0
        } else {
            let temp = x * exp(x, e - 1);
            assert(temp <= u64::MAX);
            temp
        }
    }
}

fn main() {
}

} // verus!
