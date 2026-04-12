use vstd::prelude::*;

verus! {

pub open spec fn mult(x: nat, y: nat) -> nat {
    x * y
}

fn mult_func(x: u64, y: u64) -> (r: u64)
    requires
        x > 0 && y > 0,
        x * y < u64::MAX,
    ensures
        r == mult(x as nat, y as nat),
{
    let r: u64 = x * y;
    r
}


}
