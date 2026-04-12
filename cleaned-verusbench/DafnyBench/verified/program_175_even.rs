use vstd::prelude::*;

verus! {

// Specification function for even number
spec fn even(n: u64) -> bool
    recommends
        true,
{
    n % 2 == 0
}

// Proof function to check if a number is even
fn even_func(n: u64) -> (r: bool)
    requires
        true,
    ensures
        r == even(n),
{
    n % 2 == 0
}

fn main() {
}

} // verus!
