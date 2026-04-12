use vstd::prelude::*;

verus! {

// Specification function
spec fn f(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else if n % 2 == 0 {
        1 + 2 * f(n / 2)
    } else {
        2 * f(n / 2)
    }
}

// Function to compute f(n)
fn mod_func(n: u64) -> (a: u64)
    requires
        n > 0,
    ensures
        a <= u64::MAX,
{
    let mut x: u64 = 0;
    let mut y: u64 = 1;
    let mut k: u64 = n;
    while k > 0
        invariant
        decreases k,
    {
        if k % 2 == 0 {
            if y < u64::MAX / 2 {
                y = y * 2;
            } else {
                y = u64::MAX;
            }
            if x < u64::MAX - y {
                x = x + y;
            } else {
                x = u64::MAX;
            }
            k = k / 2;
        } else {
            if y < u64::MAX / 2 {
                y = y * 2;
            } else {
                y = u64::MAX;
            }
            k = k / 2;
        }
    }
    let temp: u128 = x as u128 + y as u128;
    let x_plus_y: u64 = temp as u64;
    x_plus_y
}

fn main() {
}

} // verus!
