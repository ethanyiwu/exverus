use vstd::prelude::*;

verus! {

// Specification function to check if a number is odd
spec fn is_odd(x: int) -> bool {
    x % 2 == 1
}

// Specification function for odd numbers
spec fn odd(n: int) -> int
    recommends
        is_odd(n),
{
    n
}

// Implementation of odd numbers
fn odd_exec(n: int) -> (result: int)
    requires
        is_odd(n),
    ensures
        result == n,
{
    n
}

fn main() {
}

} // verus!
