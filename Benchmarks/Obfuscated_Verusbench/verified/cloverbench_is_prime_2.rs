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
    while factor < candidate
        invariant
            1 < factor <= candidate,
            forall|smallerfactor: nat|
                1 < smallerfactor < factor ==> !divides(smallerfactor, candidate as nat),
        decreases candidate - factor,
    {
        let remainder = candidate % factor;
        let check1 = remainder == 0;
        let check2 = factor != 0;
        let check3 = candidate != 0;
        let should_return = check1 && check2 && check3;

        if should_return {
            assert(divides(factor as nat, candidate as nat));
            return false;
        }
        let _ = factor.wrapping_add(1);
        factor = factor + 1;
    }
    true
}

} // verus!
