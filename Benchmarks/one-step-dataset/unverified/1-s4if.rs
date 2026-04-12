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
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            a.len() == N,
            sum.len() == 1,
            N > 0,
            N < 1000,
            // Add the invariant to the first loop
            forall |k: int| 0 <= k < i as int ==> a[k] == 4,  // Elements 0..i are set to 4
            forall |k: int| i as int <= k < a.len() ==> a[k] == old(a)[k],  // Elements i..end unchanged
        decreases (N as usize - i),
    {
        a.set(i, 4);
        i = i + 1;
    }

    // Add assert to verify the array is fully initialized with 4s
    assert(forall |k: int| 0 <= k < a.len() ==> a[k] == 4);

    i = 0;
    assert(sum[0] == 0); // Added by AI
    assert(4 * (i as i32) == 0); // Added by AI
    while (i < N as usize)
        invariant
            a.len() == N,
            sum.len() == 1,
            N > 0,
            N < 1000,
            forall |k: int| 0 <= k < a.len() ==> a[k] == 4,  // Array a is never modified in this loop
            sum[0] == 4 * (i as i32),  // Track the current sum value
        decreases (N as usize - i),
    {
        if (a[i] == 4) {
            let temp = sum[0];
            // Add bound assertion to prevent overflow
            assert(temp + a[( i ) as int] <= 4 * N) by {
                // Since temp == 4 * (i as i32) and we're adding 4,
                // the result is 4 * (i as i32 + 1) ≤ 4 * N
            }
            assert(temp + a[( i ) as int] <= i32::MAX) by {
                // 4 * N < 4 * 1000 = 4000, which is much less than i32::MAX
            }
            sum.set(0, temp + a[i]);
        } else {
            let temp = sum[0];
            sum.set(0, temp * a[i]);
        }
        i = i + 1;
    }
}
}

//             sum[0] == 4 * (i as i32),  // Track the current sum value
//   None: sum[0] == 4 * (i as i32)

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 2
// Safe: True