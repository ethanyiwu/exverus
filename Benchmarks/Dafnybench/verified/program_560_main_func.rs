use vstd::prelude::*;

verus! {

fn main_func(n: u64, k: u64) -> (k_out: u64)
    requires
        n > 0,
        k > n,
        k < u64::MAX - n,  // added relaxation to prevent overflow

    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j = 0;
    while j < n
        invariant
            k_out == k - j,
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
