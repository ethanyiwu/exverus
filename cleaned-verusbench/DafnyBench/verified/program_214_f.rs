use vstd::prelude::*;

verus! {

fn f(x: int, y: int) -> (r: int)
    requires
        true,
    ensures
        r == x + y,
{
    x + y
}

fn main() {
}

} // verus!
