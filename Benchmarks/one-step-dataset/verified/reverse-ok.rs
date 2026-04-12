use vstd::prelude::*;
fn main() {}

verus!{

#[verifier::loop_isolation(false)]
fn reverse(v: &mut Vec<u64>)
    ensures
        v.len() == old(v).len(),
        forall|i: int| 0 <= i < old(v).len() ==> v[i] == old(v)[old(v).len() - i - 1],
{
    let length = v.len();
    let mut n: usize = 0;
    while n < length / 2
        invariant
            n <= length / 2,
            v.len() == length,
            forall|j: int| 0 <= j < n ==> v[j] == old(v)[length - 1 - j],
            forall|j: int| n <= j < length - n ==> v[j] == old(v)[j],
            forall|j: int| length - n <= j < length ==> v[j] == old(v)[length - 1 - j],
        decreases (length / 2 - n) as int,
    {
        let x = v[n];
        let y = v[length - 1 - n];
        v.set(n, y);
        v.set(length - 1 - n, x);

        n = n + 1;
    }
}
}

// failed this postcondition
//         forall|i: int| 0 <= i < old(v).len() ==> v[i] == old(v)[old(v).len() - i - 1],
// at the end of the function body
//     while n < length / 2
//   at the end of the function body: while n < length / 2
//   failed this postcondition: forall|i: int| 0 <= i < old(v).len() ==> v[i] == old(v)[old(v).len() - i - 1]

// Compilation Error: False, Verified: 1, Errors: 0, Verus Errors: 0
// Safe: True