use vstd::prelude::*;

verus! {

spec fn even(n: nat) -> bool {
    n % 2 == 0
}

// Automatic proof function
fn even_func(n: u64) -> (r: bool)
    requires
        n < u64::MAX / 2,
    ensures
        r <==> even(n as nat),
{
    n % 2 == 0
}

fn main() {
}

} // verus!
