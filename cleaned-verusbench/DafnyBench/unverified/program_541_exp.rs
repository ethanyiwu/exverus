use vstd::prelude::*;

verus! {

# [doc = " Proof function to calculate the exponentiation"]
fn exp(b: u64, n: u64) -> (result: u128)
    requires
        n < 1000000,
        n < u64::MAX / u64::MAX,
    ensures
        result == n * (n + 1) / 2,
{
    let mut i: u64 = 0;
    let mut x: u128 = 0;
    let mut y: u128 = 1;
    while i < n {
        x = y;
        y = x + y;
        i = i + 1;
    }
    x
}


}
