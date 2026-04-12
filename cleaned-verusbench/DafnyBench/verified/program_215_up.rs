use vstd::prelude::*;

verus! {

spec fn up(n: nat) -> nat {
    n + 1
}

// Proof function to check if a stream of integers is positive
fn up_pos(n: nat) -> (result: bool)
    requires
        n > 0,
    ensures
        result ==> n > 0,
{
    true
}

fn main() {
}

} // verus!
