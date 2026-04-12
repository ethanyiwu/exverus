use vstd::prelude::*;

fn main() {}
verus! {

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
    let mut current: u64 = 1;
    let mut shadow: u64 = candidate.wrapping_sub(1);
    let mut mix: u64 = 0x5A5A5A5A5A5A5A5A;

    while current < candidate - 1 {
        current = current + 1;
        shadow = shadow.wrapping_sub(1);
        mix = mix.wrapping_add(current ^ shadow);

        if !(candidate % current != 0) {
            return false;
        }
    }
    true
}

} // verus!
