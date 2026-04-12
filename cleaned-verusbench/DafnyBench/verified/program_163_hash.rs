use vstd::prelude::*;

verus! {

// Target function
pub fn hash(key: u64) -> (h: u64)
    requires
        key < u64::MAX,
    ensures
        h >= 0,
{
    key % 1000000
}

fn main() {
}

} // verus!
