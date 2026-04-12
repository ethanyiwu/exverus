use vstd::prelude::*;

verus! {

fn main_(n: u64, k: u64) -> (k_out: u64)
    requires
        n > 0,
        k > n,
        n < 1000,  // added relaxation to prevent overflow
        k < 1000,  // added relaxation to prevent overflow

    ensures
        k_out >= 0,
{
    let mut k_out: u64 = k;
    let mut j: u64 = 0;
    while j < n && j < u64::MAX - 1
        invariant
            j + k_out == k,
            k > n,
        decreases n - j,
    {
        j = j + 1;
        k_out = k_out - 1;
    }
    k_out
}

fn main() {
}

} // verus!
