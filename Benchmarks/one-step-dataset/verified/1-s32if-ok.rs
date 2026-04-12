use vstd::prelude::*;
fn main() {}
verus!{

#[verifier::loop_isolation(false)]
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    while (i < N)
        invariant
            N > 0,
            N < 1000,
            a.len() == N,
            sum.len() == 1,
            // Add invariant that all processed elements are 1
            forall |k: int| 0 <= k < i ==> a[k] == 1,
            // All unprocessed elements remain unchanged
            forall |k: int| i <= k < a.len() ==> a[k] == old(a)[k],
            sum[0] == 0,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    // Assert that all elements are now 1 after first loop
    assert(forall |k: int| 0 <= k < a.len() ==> a[k] == 1);

    i = 0;
    while (i < N)
        invariant
            N > 0,
            N < 1000,
            a.len() == N,
            sum.len() == 1,
            // All processed elements are now 4
            forall |k: int| 0 <= k < i ==> a[k] == 4,
            // All unprocessed elements are still 1
            forall |k: int| i <= k < a.len() ==> a[k] == 1,
            sum[0] == 0,
        decreases N - i,
    {
        if (a[i] == 1) {
            let temp = a[i];
            a.set(i, temp + 3);
        } else {
            let temp = a[i];
            assert(temp >= 1) by {
                // Based on the invariant, temp should be either 1 or 4
            };
            a.set(i, temp - 1);
        }
        i = i + 1;
    }

    // Assert that all elements are now 4 after second loop
    assert(forall |k: int| 0 <= k < a.len() ==> a[k] == 4);

    i = 0;
    assert(sum[0] == 0);
    while (i < N)
        invariant
            N > 0,
            N < 1000,
            a.len() == N,
            sum.len() == 1,
            // Now this invariant holds because we've asserted it above
            forall |k: int| 0 <= k < a.len() ==> a[k] == 4,
            sum[0] == 4 * i,
            i <= N, // Added by AI, for assertion fail
        decreases N - i,
    {
        if (a[i] == 4) {
            let temp = sum[0];
            assert(temp + a[( i ) as int] <= 4 * N) by {
                // sum[0] == 4 * i from invariant
                // a[i] == 4 from invariant
                // So temp + a[i] = 4*i + 4 = 4*(i+1)
                // Since i < N, 4*(i+1) <= 4*N
            };
            assert(temp + a[( i ) as int] <= 2147483647) by {
                // 4 * N < 4 * 1000 = 4000
                // 4000 is much less than i32::MAX (2147483647)
            };
            sum.set(0, temp + a[i]);
        } else {
            let temp = sum[0];
            sum.set(0, temp * a[i]);
        }
        i = i + 1;
    }

}
}
// Score: (1, 0)
// Safe: True