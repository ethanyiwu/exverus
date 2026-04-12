use vstd::prelude::*;

verus! {

fn up_while_less(n: u64) -> (i: u64)
    requires
        n < u64::MAX - 1,  // added a limit to prevent overflow

    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i < n {
        i = i + 1;
    }
    i
}

fn up_while_not_equal(n: u64) -> (i: u64)
    requires
        n < u64::MAX - 1,  // added a limit to prevent overflow

    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i != n {
        i = i + 1;
    }
    i
}

fn down_while_not_equal(n: u64) -> (i: u64)
    requires
        n <= u64::MAX,  // added a limit to prevent overflow

    ensures
        i == 0,
{
    let mut i: u64 = n;
    while i != 0
        invariant
            0 <= i <= n,
        decreases i,
    {
        i = i - 1;
    }
    i
}

fn down_while_greater(n: u64) -> (i: u64)
    requires
        n <= u64::MAX,  // added a limit to prevent overflow

    ensures
        i == 0,
{
    let mut i: u64 = n;
    while 0 < i
        invariant
            0 <= i <= n,
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
            0 <= y && 7 * x + y == 191,
        decreases y,
    {
        y = y - 7;
        x = x + 1;
    }
    assert(x * 7 + y == 191);
}

fn quotient1() {
    let mut x: u64 = 0;
    let mut y: u64 = 191;
    assert(x * 7 + y == 191);
    x = 27;
    y = 2;
    assert(x * 7 + y == 191);
}

fn main() {
}

} // verus!
