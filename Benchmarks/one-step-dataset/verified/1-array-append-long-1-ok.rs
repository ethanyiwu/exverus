use vstd::prelude::*;

fn main() {}
verus! {

#[verifier::loop_isolation(false)]
fn append(v: &Vec<u64>, elem: u64) -> (c: Vec<u64>)
    requires
        v.len() <= 100,
    ensures
        c@.len() == v@.len() + 1,
        forall|i: int| (0 <= i && i < v.len()) ==> c[i] == v[i],
        c@.last() == elem,
{
    let mut c = Vec::with_capacity(v.len() + 1);
    let len_usize: usize = v.len();
    let mut n: usize = 0;
    let mut dummy: u8 = 0;
    while !(n == len_usize)
        invariant
            v.len() <= 100,
            c.len() == n,
            forall|k: int| 0 <= k < n ==> c[k] == v[k],
            forall|k: int| 0 <= k < v.len() ==> v[k] == v@[k],
            v.len() == len_usize,
            n <= len_usize,
            dummy <= n as u8,  // Track dummy's maximum possible value
        decreases
            len_usize - n,
    {
        c.push(v[n]);
        n = n + 1;
        
        // Assert that dummy + 1 won't overflow
        assert(dummy + 1 <= 255u8) by {
            // Since n <= 100 and dummy <= n, dummy can be at most 100
            // and 100 + 1 = 101 < 255, so no overflow
        };
        
        dummy = (dummy + 1) % 2;
    }
    c.push(elem);
    c
}

} // verus!

// failed this postcondition
//         forall|i: int| (0 <= i && i < v.len()) ==> c[i] == v[i],
// at the end of the function body
//     c
//   at the end of the function body: c
//   failed this postcondition: forall|i: int| (0 <= i && i < v.len()) ==> c[i] == v[i]

// Compilation Error: False, Verified: 1, Errors: 0, Verus Errors: 0
// Safe: True