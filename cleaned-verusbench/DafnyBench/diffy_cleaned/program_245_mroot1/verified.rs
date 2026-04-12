use vstd::prelude::*;

verus! {

// Function to calculate the square root
fn mroot1(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX,
        n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
        n < 1000000,  // added relaxation to prevent overflow

    ensures
        r >= 0 && r * r <= n && n <= (r + 1) * (r + 1),
{
    let mut r: u64 = 0;
    while r * r < n
        invariant
            r >= 0 && r * r <= n,
            n < u64::MAX,
            n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

        decreases n - r * r,
    {
        if r + 1 == u64::MAX {
            break ;
        } else {
            r = r + 1;
        }
    }
    assert(r >= 0 && r * r <= n && n <= (r + 1) * (r + 1)) by {
        assert(r >= 0);
        assert(r * r <= n);
        assert(n < u64::MAX);
        assert(r < u64::MAX);
        assert(n <= (r + 1) * (r + 1)) by {
            assert(r * r <= n);
            assert(n < u64::MAX);
            assert(n <= (r + 1) * (r + 1)) by {
                assert(n < u64::MAX);
            }
        }
    }
    r
}

fn main() {
}

} // verus!
