
use vstd::prelude::*;
fn main() {}
verus!{

#[verifier::loop_isolation(false)]
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 5 * N,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            a.len() == N,
            sum.len() == 1,
            N > 0,
            N < 1000,
            i <= N as usize,
            forall |k: int| 0 <= k < i ==> a[k] == 1,  // All processed elements are 1
            forall |k: int| i <= k < a.len() ==> a[k] == old(a)[k],  // Unprocessed elements unchanged
            sum[0] == 0, // Added by AI, for assertion fail
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize)
        invariant
            a.len() == N,
            sum.len() == 1,
            N > 0,
            N < 1000,
            i <= N as usize,
            forall |k: int| 0 <= k < i ==> a[k] == 5,  // Key invariant: all processed elements are 5
            forall |k: int| i <= k < a.len() ==> a[k] == 1,  // Unprocessed elements are still 1
        decreases N as usize - i,
    {
        if (a[i] == 1) {
            let temp = a[i];
            a.set(i, temp + 4);
        } else {
            let temp = a[i];
            // Add assertion to prevent underflow
            assert(temp >= 1) by {
                // The invariant guarantees that all processed elements (including current) are >= 1
            };
            a.set(i, temp - 1);
        }
        i = i + 1;
    }

    i = 0;
    while (i < N as usize)
        invariant
            a.len() == N,
            sum.len() == 1,
            N > 0,
            N < 1000,
            i <= N as usize,
            forall |k: int| 0 <= k < a.len() ==> a[k] == 5,  // Now this holds at the beginning
            sum[0] == 5 * (i as i32),  // Track the current sum
        decreases N as usize - i,
    {
        let temp = sum[0];
        // Add assertion to prevent overflow
        assert(temp + a[( i ) as int] <= 5 * N) by {
            // Since a[i] == 5 and temp == 5 * (i as i32)
            // temp + a[i] == 5 * (i as i32) + 5 == 5 * ((i as i32) + 1)
            // And since i < N as usize, we have (i as i32) + 1 <= N
        };
        sum.set(0, temp + a[i]);
        i = i + 1;
    }
}
}


//             forall |k: int| 0 <= k < a.len() ==> a[k] == 5,
//   None: forall |k: int| 0 <= k < a.len() ==> a[k] == 5

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 1
// Safe: True