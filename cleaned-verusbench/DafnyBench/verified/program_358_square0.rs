use vstd::prelude::*;

verus! {

/// Function to calculate the square of a number
fn square0(n: u64) -> (sqn: u64)
    requires
        n >= 0,
        n * n < u64::MAX,  // added check to prevent overflow

    ensures
        sqn == n * n,
{
    let mut sqn: u64 = n * n;
    sqn
}

fn main() {
}

} // verus!
