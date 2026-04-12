use vstd::prelude::*;

verus! {

fn negate(x: int) -> (result: int)
    ensures
        result == -x,
{
    -x
}

fn main() {
}

} // verus!
