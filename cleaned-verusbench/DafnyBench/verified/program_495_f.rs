use vstd::prelude::*;

verus! {

proof fn f() -> (r: nat)
    ensures
        r == 0,
{
    let ghost x: nat = 0;
    assert(true);
    0
}

fn main() {
}

} // verus!
