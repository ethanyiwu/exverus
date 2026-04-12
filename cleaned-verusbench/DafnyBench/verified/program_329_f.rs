use vstd::prelude::*;

verus! {

proof fn f() -> (r: nat)
    ensures
        r == 0,
{
    let x: int = 0;
    assert(true);
    0
}

fn main() {
}

} // verus!
