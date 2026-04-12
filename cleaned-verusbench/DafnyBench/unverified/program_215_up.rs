use vstd::prelude::*;

verus! {

spec fn up(n: nat) -> nat {
    n + 1
}

fn up_pos(n: nat) -> (result: bool)
    requires
        n > 0,
    ensures
        result ==> n > 0,
{
    true
}


}
