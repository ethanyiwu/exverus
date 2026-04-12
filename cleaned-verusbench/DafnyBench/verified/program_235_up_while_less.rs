use vstd::prelude::*;

verus! {

/// Function to count up while less
fn up_while_less(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            0 <= i && i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

/// Function to count up while not equal
fn up_while_not_equal(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i != n
        invariant
            0 <= i && i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

/// Function to count down while not equal
fn down_while_not_equal(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while i != 0
        invariant
            0 <= i && i <= n,
        decreases i,
    {
        i = i - 1;
    }
    i
}

/// Function to count down while greater
fn down_while_greater(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while i > 0
        invariant
            0 <= i && i <= n,
        decreases i,
    {
        i = i - 1;
    }
    i
}

fn main() {
}

} // verus!
