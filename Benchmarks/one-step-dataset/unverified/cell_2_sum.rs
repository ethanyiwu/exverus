use vstd::prelude::*;
fn main() {}
verus!{

#[verifier::loop_isolation(false)]
pub fn myfun(a: &mut Vec<u32>, N: u32) -> (sum: u32)
    requires 
        old(a).len() == N,
        N <= 0x7FFF_FFFF,
    ensures
        sum <= 2 * N,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            N <= 0x7FFF_FFFF,
            a.len() == N,
            // Add the invariant that processed elements are ≤ 2
            forall |k: int| 0 <= k < i ==> a[k] <= 2,
        decreases (N as usize) - i,
    {
        if a[i] > 2 
        {
            a.set(i, 2);
        } 
        i = i + 1;
    }

    // Add assertion after first loop to establish the property
    assert(forall |k: int| 0 <= k < a.len() ==> a[k] <= 2);

    i = 0;
    let mut sum: u32 = 0;
    
    while (i < N as usize)
        invariant
            N <= 0x7FFF_FFFF,
            a.len() == N,
            forall |k: int| 0 <= k < a.len() ==> a[k] <= 2,
            sum <= 2 * (i as u32),
        decreases (N as usize) - i,
    {
        assert(sum + a[( i ) as int] <= 2 * N) by {
            assert(2 * N <= 0xFFFF_FFFE);
        }
        sum = sum + a[i];
        i = i + 1;
    }

    proof {
        assert(sum <= 2 * N); // Added by AI
    }
    sum
}
}

// failed this postcondition
//         sum <= 2 * N,
// at the end of the function body
//     sum
//   at the end of the function body: sum
//   failed this postcondition: sum <= 2 * N

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 1
// Safe: True