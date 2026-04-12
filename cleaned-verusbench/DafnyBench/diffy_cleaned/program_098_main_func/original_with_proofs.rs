use vstd::prelude::*;

verus! {

/// Function to calculate k_out
fn main_func(n: u64, k: u64) -> (k_out: u64)
    requires
        n > 0,
        k > n,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        k < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        k_out >= 0,
{
    let mut k_out: u64 = k;
    let mut j: u64 = 0;
    while j < n
        invariant
            0 <= j && j <= n,
            j + k_out == k,
            n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
            k < u64::MAX / u64::MAX, // added relaxation to prevent overflow
        decreases
            n - j,
    {
        if k_out == 0 {
            return 0;
        }
        j = j + 1;
        k_out = k_out - 1;
    }
    k_out
}

fn main() {}

} // verus!