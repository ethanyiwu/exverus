use vstd::prelude::*;

verus! {

/// Computes the value of the Fusc sequence at a given index.
fn compute_fusc(n: u64) -> (b: u64)
    requires
        n >= 0,
    ensures
// implement the ensures clause based on the rules provided

        true,
{
    let mut b = 0;
    let mut a = 1;
    let mut n_mut = n;
    while n_mut != 0
        invariant
            0 <= n_mut <= n,
            // implement the invariant based on the rules provided
            true,
        decreases n_mut,
    {
        if n_mut % 2 == 0 {
            if a < u64::MAX - b {
                a += b;
                n_mut /= 2;
            } else {
                break ;
            }
        } else {
            if b < u64::MAX - a {
                b += a;
                n_mut = (n_mut - 1) / 2;
            } else {
                break ;
            }
        }
    }
    b
}

fn main() {
}

} // verus!
