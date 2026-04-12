use vstd::prelude::*;

verus! {

/// Function to calculate k_out
fn main_func(n: i32, k: i32) -> (k_out: i32)
    requires
        n > 0,
        k > n,
    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j: i32 = 0;
    while j < n
        invariant
            0 <= j && j <= n,
            j + k_out == k,
            0 <= k_out,
            n > 0,
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
