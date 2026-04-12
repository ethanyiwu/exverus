use vstd::prelude::*;

verus! {

fn square(n: u64) -> (r: u64)
    requires
        0 <= n,
        n < 1000000,  // added requires clause to prevent overflow
        n * n < u64::MAX,  // added requires clause to prevent overflow

    ensures
        r == n * n,
{
    n * n
}

fn main() {
}

} // verus!
