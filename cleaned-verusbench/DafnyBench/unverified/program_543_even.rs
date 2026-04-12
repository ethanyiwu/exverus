use vstd::prelude::*;

verus! {

spec fn even(n: nat) -> bool {
    n % 2 == 0
}

fn is_even(n: u64) -> (r: bool)
    requires
        n >= 0,
    ensures
        r <==> even(n as nat),
{
    let mut i: u64 = 0;
    let mut r: bool = true;
    while i < n {
        r = !r;
        i = i + 1;
    }
    r
}


}
