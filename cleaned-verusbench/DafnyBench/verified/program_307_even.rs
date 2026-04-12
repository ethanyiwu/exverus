use vstd::prelude::*;

verus! {

/// Specification function to check if a number is even
pub open spec fn even(n: nat) -> bool {
    n % 2 == 0
}

/// Proof function to check if a number is even
fn is_even(n: u64) -> (result: bool)
    requires
        n >= 0,
    ensures
        result <==> even(n as nat),
{
    n % 2 == 0
}

fn main() {
}

} // verus!
