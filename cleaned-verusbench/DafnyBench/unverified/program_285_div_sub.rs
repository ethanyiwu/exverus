use vstd::prelude::*;

verus! {

fn div_sub(a: u64, b: u64) -> (result: u64)
    requires
        a >= 0,
        b > 0,
    ensures
        result == a / b,
{
    let temp: u64 = a / b;
    temp
}

fn mod_sub(a: u64, b: u64) -> (result: u64)
    requires
        a >= 0,
        b > 0,
    ensures
        result == a % b,
{
    let temp: u64 = a % b;
    temp
}


}
