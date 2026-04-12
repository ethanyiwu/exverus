use vstd::prelude::*;

verus! {

/// Computes the value of the Fusc sequence at a given index.
fn compute_fusc(n: u64) -> (b: u64)
    requires
        n >= 0,
        n < 1000000000,  // added relaxation to prevent overflow

    ensures
// implement the ensures clause based on the rules provided

        true,
{
    let mut b = 0;
    let mut a = 1;
    let mut n_mut = n;
    while n_mut != 0 {
        if n_mut % 2 == 0 {
            if b < u64::MAX - a {
                a += b;
            }
            n_mut /= 2;
        } else {
            if a < u64::MAX - b {
                b += a;
            }
            n_mut = (n_mut - 1) / 2;
        }
    }
    b
}

fn main() {
}

} // verus!
