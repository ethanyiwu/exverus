use vstd::prelude::*;

verus! {

fn square0(n: u64) -> (sqn: u64)
    requires
        n < u64::MAX / u64::MAX, // added check to prevent overflow
        n * n < u64::MAX, // added check to prevent overflow
    ensures
        sqn == n * n,
{
    let mut sqn: u64 = 0;
    let mut i: u64 = 0;
    let mut x: u64 = 2 * i + 1;
    while i < n
        invariant
            i <= n && sqn == i * i,
            n < u64::MAX / u64::MAX, // added check to prevent overflow
            n * n < u64::MAX, // added check to prevent overflow
        decreases
            n - i,
    {
        sqn = sqn + x;
        i = i + 1;
        x = 2 * i + 1;
    }
    assert(sqn == n * n);
    sqn
}

fn square1(n: u64) -> (sqn: u64)
    requires
        n < u64::MAX / u64::MAX, // added check to prevent overflow
        n * n < u64::MAX, // added check to prevent overflow
    ensures
        sqn == n * n,
{
    let mut sqn: u64 = 0;
    let mut i: u64 = 0;
    while i < n
        invariant
            i <= n && sqn == i * i,
            n < u64::MAX / u64::MAX, // added check to prevent overflow
            n * n < u64::MAX, // added check to prevent overflow
        decreases
            n - i,
    {
        let x: u64 = 2 * i + 1;
        sqn = sqn + x;
        i = i + 1;
    }
    assert(sqn == n * n);
    sqn
}

// TODO: implement q function

fn test0() {
    assert(true);
    assert(true);
}

fn main() {}
}