use vstd::prelude::*;

verus! {

# [doc = " Specification function for fusc"]
spec fn fusc(n: u64) -> u64 {
    n
}

# [doc = " Proof function for fusc"]
fn fusc_proof(n: u64) -> (result: u64)
    requires
        n >= 0,
    ensures
        result == fusc(n),
{
    let mut result: u64 = n;
    result
}

fn compute_fusc(n: u64) -> (result: u64)
    requires
        n >= 0,
    ensures
        result == fusc(n),
{
    fusc_proof(n)
}


}
