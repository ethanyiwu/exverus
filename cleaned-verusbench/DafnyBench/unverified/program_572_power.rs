use vstd::prelude::*;

verus! {

# [doc = " Specification function for power"]
spec fn power(n: int, alpha: int) -> int {
    n * alpha
}

# [doc = " Proof function for power"]
fn power_func(n: u64, alpha: u64) -> (product: u64)
    requires
        n > 0,
        alpha > 0,
        n < 1000,
        n * alpha < u64::MAX,
    ensures
        product == n * alpha,
{
    let product = n * alpha;
    product
}


}
