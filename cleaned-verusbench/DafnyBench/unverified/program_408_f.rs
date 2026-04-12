use vstd::prelude::*;

verus! {

fn f(x: u64, y: u64) -> (result: u64)
    ensures
        result == 0,
{
    let x: u64 = 0;
    0
}


}
