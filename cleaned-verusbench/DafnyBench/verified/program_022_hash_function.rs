use vstd::prelude::*;

verus! {

// Target function
pub fn hash_function(key: u64) -> (hash: u64)
    requires
        key >= 0,
    ensures
        hash >= 0,
{
    let mut hash: u64 = key % 1000000;
    hash
}

fn main() {
}

} // verus!
