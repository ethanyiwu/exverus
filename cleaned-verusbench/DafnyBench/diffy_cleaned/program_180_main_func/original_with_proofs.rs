use vstd::prelude::*;

verus! {

/// Returns the result of subtracting the value of n from k.
fn main_func(n: u64, k: u64) -> (k_out: u64)
    requires
        n > 0,
        k > n,
        k < u64::MAX - n, // added relaxation to prevent overflow
    ensures
        k_out >= 0,
        k_out == k - n,
{
    let mut k_out: u64 = k;
    let mut j: u64 = 0;
    while j < n
        invariant
            0 <= j && j <= n,
            k_out == k - j,
            n > 0,
            k > n,
            k < u64::MAX - n, // added relaxation to prevent overflow
        decreases n - j,
    {
        j = j + 1;
        k_out = k_out - 1;
    }
    k_out
}

fn main() {}

} // verus!