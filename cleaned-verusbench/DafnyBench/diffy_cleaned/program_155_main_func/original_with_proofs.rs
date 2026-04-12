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
    while j < n
        invariant
            0 <= j && j <= n,
            j + k_out == k,
            k > n,
            k < u64::MAX,
        decreases
            n - j,
    {
        j = j + 1;
        k_out = k_out - 1;
    }
    assert(k_out >= 0); // REVIEW:                 ^^^^^^^^^^^ expected `u64`, found `int`
    assert(k_out == k - n); // REVIEW:                  ^^^^^^^^^^ expected `u64`, found `int`
    k_out
}

fn main() {}

} // verus!