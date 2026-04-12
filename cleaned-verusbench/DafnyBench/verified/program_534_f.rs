use vstd::prelude::*;

verus! {

fn f(x: u64, y: u64) -> (result: u64)
    requires
        x < 1000000,  // Adding a precondition to limit the input size of x
        y < 1000000,  // Adding a precondition to limit the input size of y
        x * 13 < u64::MAX,  // Adding a precondition to prevent overflow

    ensures
        result == 13 * x,
{
    let mut result: u64 = x * 13;
    result
}

fn g(x: u64, y: u64) -> (result: u64)
    requires
        x < 1000000,  // Adding a precondition to limit the input size of x
        y < 1000000,  // Adding a precondition to limit the input size of y
        x * 13 < u64::MAX,  // Adding a precondition to prevent overflow

    ensures
        result == 13 * x,
{
    let mut result: u64 = x * 13;
    result
}

fn h(x: i32, y: u64) -> (result: i32)
    requires
        x >= i32::MIN && x <= i32::MAX,
        y < 1000000,  // Adding a precondition to limit the input size of y

    ensures
        result == x,
{
    let mut result: i32 = x;
    result
}

fn j(x: i32) -> (result: i32)
    requires
        x >= i32::MIN && x <= i32::MAX,
    ensures
        result == x,
{
    let mut result: i32 = x;
    result
}

fn k(x: i32, y: u64) -> (result: i32)
    requires
        x >= i32::MIN && x <= i32::MAX,
        y < 1000000,  // Adding a precondition to limit the input size of y

    ensures
        result == x,
{
    let mut result: i32 = x;
    result
}

fn main() {
}

} // verus!
