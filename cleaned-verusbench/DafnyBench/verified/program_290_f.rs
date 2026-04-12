use vstd::prelude::*;

verus! {

fn f(x: int, y: int) -> (result: int)
    requires
        x >= 0,
        y >= 0,
    ensures
        result >= 0,
{
    x + y
}

fn main() {
}

} // verus!
