use vstd::prelude::*;

fn main() {}
verus! {

#[verifier::loop_isolation(false)]

fn copy(a: &Vec<u64>) -> (b: Vec<u64>)
    requires
        a.len() <= 100,
    ensures
        b@.len() == a@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> b[i] == a[i],
{
    let mut b = Vec::with_capacity(a.len());
    let len: usize = a.len();
    let mut idx: usize = 0;
    let mut counter: usize = len.wrapping_add(1);

    while idx < len
        invariant
            a@.len() == len,
            b@.len() == idx,
            forall|i: int| 0 <= i < idx ==> b[i] == a[i], // Added by AI
        decreases len - idx,
    {
        b.push(a[idx]);
        idx = idx + 1;
        counter = counter.wrapping_sub(1);
        let _ = counter;
    }
    proof {
        assert(b@.len() == len); // Added by AI
    }
    b
}

} // verus!

// failed this postcondition
//         b@.len() == a@.len(),
// at the end of the function body
//     b
//   at the end of the function body: b
//   failed this postcondition: b@.len() == a@.len()

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 1
// Safe: True