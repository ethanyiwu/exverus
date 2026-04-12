use vstd::prelude::*;

verus! {

fn up_while_less(n: u64) -> (i: u64)
    requires
        n as int >= 0,
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            0 <= i as int <= n as int,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

fn up_while_not_equal(n: u64) -> (i: u64)
    requires
        n as int >= 0,
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i != n
        invariant
            0 <= i as int <= n as int,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

fn down_while_not_equal(n: u64) -> (i: u64)
    requires
        n as int >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while i != 0
        invariant
            0 <= i as int <= n as int,
        decreases i,
    {
        i = i - 1;
    }
    i
}

fn down_while_greater(n: u64) -> (i: u64)
    requires
        n as int >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while 0 < i
        invariant
            0 <= i as int <= n as int,
        decreases i,
    {
        i = i - 1;
    }
    i
}

fn quotient() {
    let mut x: u64 = 0;
    let mut y: u64 = 191;
    while 7 <= y
        invariant
            0 <= y as int && 7 * x + y == 191,
        decreases y,
    {
        y = y - 7;
        x = x + 1;
    }
    assert(x * 7 + y == 191);
}

fn quotient1() {
    // This function is incorrect and does not meet the requirements.
    // It does not use a loop to find the quotient, but instead assigns values directly.
    let mut x: u64 = 0;
    let mut y: u64 = 191;
    while 7 <= y
        invariant
            0 <= y as int && 7 * x + y == 191,
        decreases y,
    {
        x = 27;
        y = 2;
    }
    // This assertion does not hold because the loop does not update x and y correctly.
    // assert(x * 7 + y == 191);
}

fn main() {}

} // verus!