use vstd::prelude::*;

verus! {

proof fn f() -> (result: nat)
    ensures
        result == 0,
{
    let mut x: nat = 0;
    assert(true);
    0
}

fn main() {
}

} // verus!
