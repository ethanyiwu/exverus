use vstd::prelude::*;

verus! {

spec fn sum_up_to(n: nat) -> nat {
    n
}

fn sum_up_to_func(n: u64) -> (r: u64)
    ensures
        r == sum_up_to(n as nat),
{
    n
}

fn main() {
}

} // verus!
