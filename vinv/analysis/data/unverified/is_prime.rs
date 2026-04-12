
use vstd::prelude::*;

fn main() {}

verus! {

#[verifier::loop_isolation(false)]

spec fn divides(factor: nat, candidate: nat) -> bool {
    candidate % factor == 0
}

spec fn is_prime(candidate: nat) -> bool {
    &&& 1 < candidate
    &&& forall|factor: nat| 1 < factor && factor < candidate ==> !divides(factor, candidate)
}

fn test_prime(candidate: u64) -> (result: bool)
    requires
        1 < candidate,
    ensures
        result == is_prime(candidate as nat),
{
    let mut factor: u64 = 2;
    while factor < candidate
        invariant
            1 < candidate,
            factor > 0,
            forall|f: nat| 1 < f < factor ==> !divides(f, candidate as nat),
        decreases candidate - factor,
    {
        if candidate % factor == 0 {
            proof {
                let n_candidate = candidate as nat;
                assert(exists|factor: nat| 1 < factor <= n_candidate && divides(factor, n_candidate)); // Adjusted invariant for assertion fail
                assert(!is_prime(n_candidate));
            }
            return false;
        }
        factor = factor + 1;
    }
    proof {
        assert(forall|f: nat| 1 < f < candidate ==> !divides(f, candidate as nat));
        assert(is_prime(candidate as nat));
    }
    true
}

} // verus!

// Score: Compilation Error: False, Verified: 1, Errors: 1, Verus Errors: 2