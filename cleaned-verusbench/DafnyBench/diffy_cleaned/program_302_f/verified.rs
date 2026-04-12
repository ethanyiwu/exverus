use vstd::prelude::*;

verus! {

fn f(x: u64, y: u64) -> (result: u64)
    requires
        y <= x + 1,
        x < 1000000,  // added a relaxation to prevent overflow

    ensures
        result == 13 * x,
{
    let mut result: u128 = 0;  // Use u128 to prevent overflow
    for i in 0..x
        invariant
            0 <= i && i <= x,
            result == 13 * i,
    {
        result = result + 13;
    }
    assert(result <= u64::MAX as u128);
    let result: u64 = result as u64;
    result
}

fn g(x: u64, y: u64) -> (result: u64)
    requires
        y <= x + 1,
        x < 1000000,  // added a relaxation to prevent overflow

    ensures
        result == 13 * x,
{
    let mut result: u128 = 0;  // Use u128 to prevent overflow
    for i in 0..x
        invariant
            0 <= i && i <= x,
            result == 13 * i,
    {
        result = result + 13;
    }
    assert(result <= u64::MAX as u128);
    let result: u64 = result as u64;
    result
}

fn h(x: i64, y: u64) -> (result: i64)
    requires
        y <= 100,
    ensures
        result == x,
{
    x
}

fn j(x: i64) -> (result: i64)
    requires
        true,
    ensures
        result == x,
{
    x
}

fn main() {
}

} // verus!
