use vstd::prelude::*;

verus! {

fn f(x: int, y: int) -> (result: int)
    ensures
        result == x + y,
{
    x + y
}

fn main() {
}

} // verus!
