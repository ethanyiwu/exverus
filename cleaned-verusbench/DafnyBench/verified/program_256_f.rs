use vstd::prelude::*;

verus! {

proof fn f(x: int, y: int) -> (result: int)
    ensures
        result >= x,
        result >= y,
        result == x || result == y,
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
