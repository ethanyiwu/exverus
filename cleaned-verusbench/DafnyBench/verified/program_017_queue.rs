use vstd::prelude::*;

verus! {

/// Target function
pub fn queue() -> (result: bool)
    ensures
        result == true,
{
    assert(true);
    true
}

fn main() {
}

} // verus!
