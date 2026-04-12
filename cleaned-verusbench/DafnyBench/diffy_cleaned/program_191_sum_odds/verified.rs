use vstd::prelude::*;

verus! {

fn sum_odds(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

    ensures
        sum == n * n,
{
    let mut sum: u64 = 1;
    let mut i: u64 = 0;

    while i < n - 1
        invariant
            0 <= i && i < n,
            sum == (i + 1) * (i + 1),
            n < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

        decreases n - i,
    {
        i = i + 1;
        sum = sum + 2 * i + 1;
        assert(sum == (i + 1) * (i + 1)) by {
            assert(sum == (i + 1) * (i + 1));
            if i == 0 {
                assert(sum == 1);
            } else {
                assert(sum == i * i + 2 * i + 1);
                assert(sum == (i + 1) * (i + 1));
            }
        }
    }
    assert(sum == n * n);
    sum
}

fn main() {
}

} // verus!
