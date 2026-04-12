
use vstd::prelude::*;

fn main() {}
verus! {

#[verifier::loop_isolation(false)]
fn concat(a: &Vec<u64>, b: &Vec<u64>) -> (c: Vec<u64>)
    requires
        a.len() <= 100 && b.len() <= 100,
    ensures
        c@.len() == a@.len() + b@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> c[i] == a[i],
        forall|i: int| (a.len() <= i && i < c.len()) ==> c[i] == b[i - a.len()],
{
    let mut c = Vec::with_capacity(a.len() + b.len());
    let mut n: usize = 0;
    let len: usize = a.len() + b.len();
    let mut state: usize = 0;

    while n < len
        invariant
            a.len() <= 100,
            b.len() <= 100,
            a@.len() == a@.len(),
            b@.len() == b@.len(),
            c@.len() == n,
            state == n,  // Add invariant that state equals n
            n <= len,
            // The arrays a and b are never modified in the loop (no a.set() or b.set())
            forall |k: int| 0 <= k && k < a@.len() ==> a[k] == a[k],
            forall |k: int| 0 <= k && k < b@.len() ==> b[k] == b[k],
        decreases
            len - n,
    {
        let value = if n < a.len() {
            a[n]
        } else {
            b[n - a.len()]
        };
        c.push(value);
        n = n + 1;
        assert(state < usize::MAX);  // This should be automatically provable
        state = state + 1;
    }
    c
}

} // verus!


//         state = state + 1;
//   None: state + 1

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 2
// Safe: True