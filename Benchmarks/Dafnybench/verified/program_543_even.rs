use vstd::prelude::*;

verus! {

// Specification for even function
spec fn even(n: nat) -> bool {
    n % 2 == 0
}

// Function to check if a number is even
fn is_even(n: u64) -> (r: bool)
    requires
        n >= 0,
    ensures
        r <==> even(n as nat),
{
    let mut i: u64 = 0;
    let mut r: bool = true;

    while i < n
        invariant
            0 <= i && i <= n,
            r <==> (i % 2 == 0),
        decreases n - i,
    {
        r = !r;
        i = i + 1;
    }
    r
}

fn main() {
}

} // verus!
