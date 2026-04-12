use vstd::prelude::*;

verus! {

// Specification for even function
spec fn even(n: nat) -> bool {
    n % 2 == 0
}

// Function to check if a number is even
fn is_even(n: u64) -> (r: bool)
    requires
        n < u64::MAX,
    ensures
        r <==> even(n as nat),
{
    n % 2 == 0
}

fn main() {
}

} // verus!
