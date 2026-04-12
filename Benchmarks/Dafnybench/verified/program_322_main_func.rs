use vstd::prelude::*;

verus! {

fn main_func(n: i32, k: i32) -> (k_out: i32)
    requires
        n > 0,
        k > n,
    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j = 0;
    while j < n
        invariant
            0 <= j && j <= n,
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
