use vstd::prelude::*;

verus! {

fn main_func(n: u64, k: u64) -> (k_out: u64)
    requires
        n > 0,
        k > n,
        k < u64::MAX,
    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j = 0;
    while j < n {
        j = j + 1;
        k_out = k_out - 1;
    }
    k_out
}


}
