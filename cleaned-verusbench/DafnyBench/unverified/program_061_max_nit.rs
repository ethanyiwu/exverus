use vstd::prelude::*;

verus! {

fn max_nit(b: u64) -> (nmax: u64)
    requires
        b >= 2,
        b < 1000,
    ensures
        nmax == b - 1,
        nmax < b,
{
    b - 1
}


}
