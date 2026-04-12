
use vstd::prelude::*;
fn main() {}

verus!{

#[verifier::loop_isolation(false)]
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] <= N,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            N > 0,
            a.len() == N,
            sum.len() == 1,  // Added invariant to first loop
            forall |k: int| 0 <= k < i as int ==> a[k] == 1 || a[k] == 0,  // Added invariant
        decreases (N as usize - i),
    {
        if (i % 1 == 0) {
            a.set(i, 1);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    // Now we can assert that the entire array has values 0 or 1
    assert(forall |k: int| 0 <= k < a.len() ==> a[k] == 1 || a[k] == 0);

    i = 0;
    while (i < N as usize)
        invariant
            N > 0,
            a.len() == N,
            forall |k: int| 0 <= k < a.len() ==> a[k] == 1 || a[k] == 0,  // This should now hold
            sum.len() == 1,
            sum[0] <= i as i32,
            i as i32 <= N,
        decreases (N as usize - i),
    {
        if (i == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            
            assert(temp + a[( i ) as int] <= i32::MAX) by {
                // Since temp <= (i-1) and a[i] <= 1, and i < N <= i32::MAX
                // temp + a[i] <= (i-1) + 1 = i <= N <= i32::MAX
            }
            
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
    }
}
}


//             forall |k: int| 0 <= k < a.len() ==> a[k] == 1 || a[k] == 0,
//   None: forall |k: int| 0 <= k < a.len() ==> a[k] == 1 || a[k] == 0

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 2
// Safe: True