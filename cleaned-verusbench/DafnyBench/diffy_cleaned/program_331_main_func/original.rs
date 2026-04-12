use vstd::prelude::*;

verus! {

fn main_func(n: usize, k: usize) -> (k_out: usize)
    requires
        n > 0,
        k > n,
        k < usize::MAX - n,
        n < usize::MAX / 2,
    ensures
        k_out >= 0,
{
    let mut k_out = k;
    let mut j = 0;
    while j < n {
        j += 1;
        k_out -= 1;
    }
    k_out
}


}
