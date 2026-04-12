use vstd::prelude::*;

verus! {

spec fn is_odd(x: int) -> bool {
    x % 2 == 1
}

spec fn odd(n: int) -> int
    recommends
        is_odd(n),
{
    n
}

fn odd_exec(n: int) -> (result: int)
    requires
        is_odd(n),
    ensures
        result == n,
{
    n
}


}
