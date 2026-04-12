
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
            state == n,
            n <= len,
            forall |k: int| 0 <= k && k < a@.len() ==> a[k] == a[k],
            forall |k: int| 0 <= k && k < b@.len() ==> b[k] == b[k],
            (forall|i: int| (0 <= i && i < n) ==> 
                if i < a.len() { c[i] == a[i] } else { c[i] == b[i - a.len()] })
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
        assert(state < usize::MAX);
        state = state + 1;
    }
    c
}

} // verus!


// failed this postcondition
//         forall|i: int| (a.len() <= i && i < c.len()) ==> c[i] == b[i - a.len()],
// at the end of the function body
//     c
//   at the end of the function body: c
//   failed this postcondition: forall|i: int| (a.len() <= i && i < c.len()) ==> c[i] == b[i - a.len()]

// Compilation Error: False, Verified: 1, Errors: 0, Verus Errors: 0
// Safe: True