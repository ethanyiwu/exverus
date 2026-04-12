use vstd::prelude::*;

verus! {

spec fn add(x: nat, y: nat) -> nat {
    x + y
}

fn add_func(x: u64, y: u64) -> (s: u64)
    requires
        x > 0,
        y > 0,
        x < u64::MAX / 2,
        y < u64::MAX / 2,
        x + y < u64::MAX,
    ensures
        s == x + y,
{
    let temp: u128 = x as u128 + y as u128;
    let s: u64 = temp as u64;
    s
}


}
