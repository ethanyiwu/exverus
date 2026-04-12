use vstd::prelude::*;

verus! {

fn max(a: int, b: int) -> (result: int)
    ensures
        result >= a,
        result >= b,
{
    if a >= b {
        a
    } else {
        b
    }
}

fn main() {
}

} // verus!
