use vstd::prelude::*;

verus! {

proof fn f(x: int, y: int) -> (result: int)
    ensures
        result == x,
{
    assert(x == x);
    x
}

fn main() {
}

} // verus!
