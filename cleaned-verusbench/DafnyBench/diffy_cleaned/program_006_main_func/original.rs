use vstd::prelude::*;

verus! {

fn main_func(n: u32, k: u32) -> (k_out: u32)
    requires
        n > 0,
        k > n,
        n <= u32::MAX - 1,
    ensures
        k_out >= 0,
{
    let mut k_out: u32 = k;
    let mut j: u32 = 0;
    while j < n {
        j = j + 1;
        k_out = k_out - 1;
    }
    k_out
}


}
