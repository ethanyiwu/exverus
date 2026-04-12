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
    let mut parity: bool = true;

    while factor < candidate
        invariant
            1 < factor <= candidate,
            forall|smallerfactor: nat|
                1 < smallerfactor < factor ==> !divides(smallerfactor, candidate as nat),
        decreases candidate - factor,
    {
        let remainder = candidate % factor;
        let check1 = remainder == 0;

        if check1 {
            assert(divides(factor as nat, candidate as nat));
            return false;
        }
        factor = factor + 1;
        parity = !parity;
    }
    true
}

} // verus!
