use vstd::prelude::*;

verus! {

proof fn f(x: int, y: int) -> (result: int)
    ensures
        result == 0,
{
    let x: int = 0;
    assert(true);
    0
}

fn main() {
}

} // verus!
