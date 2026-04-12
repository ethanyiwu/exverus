use vstd::prelude::*;
use vstd::seq::*;

verus! {

fn random(a: i32, b: i32) -> (r: i32)
    requires
        a <= b,
    ensures
        a <= r && r <= b,
{
    assert(a <= b);
    a
}

fn main() {
}

} // verus!
