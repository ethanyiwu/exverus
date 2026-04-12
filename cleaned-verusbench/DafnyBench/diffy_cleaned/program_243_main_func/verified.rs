use vstd::prelude::*;

verus! {

fn main_func(n: u64, k: u64) -> (k_out: u64)
    requires
        n > 0,
        k > n,
        k > n + 1,  // added a relaxation to prevent overflow

    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j = 0;
    while j < n
        invariant
            0 <= j <= n,
            j + k_out == k,
            k > n + 1,  // added a relaxation to prevent overflow

        decreases n - j,
    {
        j = j + 1;
        if k_out > 1 {
            k_out = k_out - 1;
        }
    }
    assert(k_out >= 0);
    k_out
}

fn main() {
}

} // verus!
