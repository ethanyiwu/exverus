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
    let mut factor: u64 = 2;
    let mut alternate: bool = false;
    let mut accumulator: u64 = 0;

    while factor < candidate {
        let check_result = if alternate {
            !(candidate % factor != 0)
        } else {
            candidate % factor == 0
        };

        if check_result {
            return false;
        }
        alternate = !alternate;
        accumulator = 1 - accumulator;
        factor = factor + 1;
    }
    true
}

} // verus!
