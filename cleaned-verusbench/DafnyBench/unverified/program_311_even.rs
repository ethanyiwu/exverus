use vstd::prelude::*;

verus! {

spec fn even(n: nat) -> bool {
    n % 2 == 0
}

fn is_even(n: u64) -> (r: bool)
    requires
        n < u64::MAX,
    ensures
        r <==> even(n as nat),
{
    n % 2 == 0
}


}
