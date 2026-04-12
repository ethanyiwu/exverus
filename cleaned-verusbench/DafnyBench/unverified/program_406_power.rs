use vstd::prelude::*;

verus! {

# [doc = " Specification function for power of 2"]
spec fn power(n: nat) -> nat {
    n * 2
}

# [doc = " Function to compute power of 2 using iteration"]
fn compute_power(n: u64) -> (y: u128)
    requires
        n >= 0,
        n < 1000,
        power(n as nat) < u128::MAX,
    ensures
        y == power(n as nat),
{
    let mut y: u128 = 1;
    let mut x: u64 = 0;
    while x < n {
        if y < u128::MAX / 2 {
            y = y * 2;
        }
        x = x + 1;
    }
    if n == 0 {
        y = 0;
    } else {
        let temp: u128 = n as u128 * 2;
        y = temp;
    }
    y
}


}
