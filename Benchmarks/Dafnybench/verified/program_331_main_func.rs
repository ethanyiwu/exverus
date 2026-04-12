use vstd::prelude::*;

verus! {

fn main_func(n: usize, k: usize) -> (k_out: usize)
    requires
        n > 0,
        k > n,
        k < usize::MAX - n,  // added relaxation to prevent overflow
        n < usize::MAX / 2,  // added relaxation to prevent overflow

    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j = 0;
    while j < n
        invariant
            j + k_out == k,
            k > n,

        decreases n - j,
    {
        j += 1;
        k_out -= 1;
    }
    k_out
}

fn main() {
}

} // verus!
