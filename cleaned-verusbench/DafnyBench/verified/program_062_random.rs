use vstd::prelude::*;

verus! {

fn random(a: int, b: int) -> (r: int)
    requires
        a <= b,
    ensures
        a <= b ==> a <= r && r <= b,
{
    a
}

fn main() {
}

} // verus!
