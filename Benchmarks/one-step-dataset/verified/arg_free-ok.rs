
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
            res == 5 + idx,  // Add invariant tracking res value
        decreases(10 - idx)
    {
        res = res + 1;
        idx = idx + 1;
    }
    idx = 0;
    while (idx < 10)
        invariant
            idx <= 10,
            res == 15 + idx,  // res is 15 after first loop, then increments
        decreases(10 - idx)
    {
        
        res = res + 1;
        idx = idx + 1;
    }
    assert(res == 25);
}
}


//         res = res + 1;
//   None: res + 1

// Compilation Error: False, Verified: 1, Errors: 0, Verus Errors: 0
// Safe: True