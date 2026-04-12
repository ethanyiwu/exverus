use vstd::prelude::*;
fn main() {}

verus!{

#[verifier::loop_isolation(false)]
fn choose_odd()
{
    let mut idx: u64 = 0;
    let mut res: u64 = 5;
    while (idx < 10)
        invariant
            idx <= 10,
            res == 5 + idx,
        decreases(10 - idx) // Added by AI
    {
        res = res + 1;
        idx = idx + 1;
    }
    idx = 0;
    while (idx < 10)
        invariant
            idx <= 10,
        decreases(10 - idx) // Added by AI
    {
        res = res + 1;
        idx = idx + 1;
    }
    assert(res == 25);
}
}

//     while (idx < 10)
//   None: while (idx < 10)

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 3
// Safe: True