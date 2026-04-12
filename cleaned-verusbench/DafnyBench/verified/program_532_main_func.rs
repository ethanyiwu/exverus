use vstd::prelude::*;

verus! {

fn main_func(n: u64, k: u64) -> (k_out: i64)
    requires
        n > 0,
        k > n,
        k <= u64::MAX as i64,  // added a precondition
        k <= i64::MAX,  // added a precondition

    ensures
        k_out >= 0,
{
    let k_out = (k as i64) - (n as i64);
    k_out
}

fn main() {
}

} // verus!
