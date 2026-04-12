use vstd::arithmetic::div_mod::{
    lemma_fundamental_div_mod, lemma_fundamental_div_mod_converse_div,
};
use vstd::prelude::*;

verus! {

pub open spec fn mul(a: nat, b: nat) -> nat {
    builtin::mul(a, b)
}

/// Specification for what it means for d to divide a
pub open spec fn divides(factor: nat, candidate: nat) -> bool {
    exists|k: nat| mul(factor, k) == candidate
}

/// Implementation.
fn largest_divisor(n: u32) -> (ret: u32)
    requires
        n > 1,
    ensures
        divides(ret as nat, n as nat),
        ret < n,
        forall|k: u32| (0 < k < n && divides(k as nat, n as nat)) ==> ret >= k,
{
    let mut i = n - 1;
    while i >= 2 {
        if n % i == 0 {
            return i;
        }
        i -= 1;
    }

    1
}

} // verus!
fn main() {}
