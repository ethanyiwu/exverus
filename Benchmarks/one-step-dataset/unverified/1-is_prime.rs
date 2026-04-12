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
    while
        factor < candidate
        invariant
            1 < factor <= candidate,
        decreases
            candidate - factor, // Added by AI
    {
        if candidate % factor == 0 {
            assert(divides(factor as nat, candidate as nat));
            return false;
        }
        factor = factor + 1;
    }
    true
}

} // verus!
