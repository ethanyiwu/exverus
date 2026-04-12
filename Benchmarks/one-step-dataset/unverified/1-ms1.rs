use vstd::prelude::*;
fn main() {}
verus!{

#[verifier::loop_isolation(false)]

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize) 
    requires 
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] == 0,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            N > 0,
            a.len() == N,
            sum.len() == 1,
            forall |k: int| 0 <= k < i ==> a[k] == k % 1,  // Partial invariant for first loop
        decreases N - i,
    {
        a.set(i, i % 1 );
        i = i + 1;
    }

    // After first loop, we know the full invariant holds
    assert(forall |k: int| 0 <= k < a.len() ==> a[k] == k % 1);
    
    i = 0;
    
    while (i < N as usize)
        invariant
            N > 0,
            a.len() == N,
            sum.len() == 1,
            forall |k: int| 0 <= k < a.len() ==> a[k] == k % 1,  // Now this holds
            sum[0] == 0, // Added by AI
        decreases N - i,
    {
        if (i == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
    }
}
}

// failed this postcondition
//         sum[0] == 0,
// at the end of the function body
//     while (i < N as usize)
//   at the end of the function body: while (i < N as usize)
//   failed this postcondition: sum[0] == 0

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 1
// Safe: True