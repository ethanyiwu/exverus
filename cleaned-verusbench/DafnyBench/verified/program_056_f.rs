use vstd::prelude::*;

verus! {

spec fn f(x: nat, y: nat) -> nat {
    13 * x
}

fn f_exec(x: u64, y: u64) -> (result: u64)
    requires
        x < 1000000,  // added relaxation to prevent overflow
        y < 1000000,  // added relaxation to prevent overflow

    ensures
        result == 13 * x,
{
    x * 13
}

spec fn g(x: nat, y: nat) -> nat {
    13 * x
}

fn g_exec(x: u64, y: u64) -> (result: u64)
    requires
        x < 1000000,  // added relaxation to prevent overflow
        y < 1000000,  // added relaxation to prevent overflow

    ensures
        result == 13 * x,
{
    x * 13
}

fn h(x: u64, y: u64) -> (result: u64)
    requires
        y < 1000000,  // added relaxation to prevent overflow

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

fn k(x: u64, y: u64) -> (result: u64)
    requires
        y < 1000000,  // added relaxation to prevent overflow

    ensures
        result == x,
{
    x
}

fn main() {
}

} // verus!
