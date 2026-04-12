use vstd::prelude::*;

verus! {

/// Up while less
fn up_while_less(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: usize = 0;
    while i < n
        invariant
            0 <= i && i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

/// Up while not equal
fn up_while_not_equal(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: usize = 0;
    while i != n
        invariant
            0 <= i && i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

/// Down while not equal
fn down_while_not_equal(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: usize = n;
    while i != 0
        invariant
            0 <= i && i <= n,
        decreases i,
    {
        i = i - 1;
    }
    i
}

/// Down while greater
fn down_while_greater(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: usize = n;
    while i > 0
        invariant
            0 <= i && i <= n,
        decreases i,
    {
        i = i - 1;
    }
    i
}

/// Function to calculate the quotient
fn quotient() {
    let mut x: usize = 0;
    let mut y: usize = 191;
    while y >= 7
        invariant
            0 <= y && 7 * x + y == 191,
        decreases y,
    {
        y = y - 7;
        x = x + 1;
    }
    assert(x * 7 + y == 191);
}

/// Function to calculate the quotient
fn quotient1() {
    let mut x: usize = 0;
    let mut y: usize = 191;
    while y >= 7
        invariant
            0 <= y && 7 * x + y == 191,
        decreases y,
    {
        x = 27;
        y = 2;
    }
    assert(x * 7 + y == 191);
}

fn main() {}

} // verus!