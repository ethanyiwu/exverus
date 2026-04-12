use vstd::prelude::*;

verus! {

fn f(x: u64, _y: u64) -> (result: u64)
    requires
        x < u64::MAX / 13,
    ensures
        result == 13 * x,
{
    let mut result: u64 = 0;
    for i in 0..x {
        result += 13;
    }
    result
}

fn g(x: u64, _y: u64) -> (result: u64)
    requires
        x < u64::MAX / 13,
    ensures
        result == 13 * x,
{
    let mut result: u64 = 0;
    for i in 0..x {
        result += 13;
    }
    result
}

fn h(x: u64, _y: u64) -> (result: u64)
    requires
        true,
    ensures
        result == x,
{
    x
}

fn j(x: u64) -> (result: u64)
    requires
        true,
    ensures
        result == x,
{
    x
}

fn k(x: u64, _y: u64) -> (result: u64)
    requires
        false,
    ensures
        result == x,
{
    x
}


}
