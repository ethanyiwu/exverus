use vstd::prelude::*;

verus! {

/// Specification function for power
spec fn power(n: int, alpha: int) -> int {
    n * alpha
}

/// Proof function for power
fn power_func(n: u64, alpha: u64) -> (product: u64)
    requires
        n > 0,
        alpha > 0,
        n < 10000,  // added relaxation to prevent overflow
        alpha < 10000,  // added relaxation to prevent overflow
        n * alpha < u64::MAX,  // added relaxation to prevent overflow

    ensures
        product == n * alpha,
{
    let temp: u128 = n as u128 * alpha as u128;
    assert(temp <= u64::MAX as u128);
    let product: u64 = temp as u64;
    product
}

fn main() {
}

} // verus!
