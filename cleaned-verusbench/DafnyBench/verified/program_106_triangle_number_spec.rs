use vstd::prelude::*;

verus! {

spec fn triangle_number_spec(n: int) -> int {
    n * (n + 1) / 2
}

fn triangle_number(n: u64) -> (t: u64)
    requires
        n >= 0,
        n < 1000000,
        n * (n + 1) < u64::MAX,
    ensures
        t == n * (n + 1) / 2,
{
    n * (n + 1) / 2
}

fn main() {
}

} // verus!
