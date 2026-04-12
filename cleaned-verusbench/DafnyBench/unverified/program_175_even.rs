use vstd::prelude::*;

verus! {

spec fn even(n: u64) -> bool
    recommends
        true,
{
    n % 2 == 0
}

fn even_func(n: u64) -> (r: bool)
    requires
        true,
    ensures
        r == even(n),
{
    n % 2 == 0
}


}
