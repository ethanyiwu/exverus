use vstd::prelude::*;

verus! {

fn square(n: u64) -> (r: u64)
    requires
        0 <= n,
        n < 1000000,
        n * n < u64::MAX,
    ensures
        r == n * n,
{
    n * n
}


}
