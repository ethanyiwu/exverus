use vstd::prelude::*;

verus! {

/// Up while less
fn up_while_less(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i < n {
        i = i + 1;
    }
    i
}

/// Up while not equal
fn up_while_not_equal(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i != n {
        i = i + 1;
    }
    i
}

/// Down while not equal
fn down_while_not_equal(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while i != 0 {
        i = i - 1;
    }
    i
}

/// Down while greater
fn down_while_greater(n: u64) -> (i: u64)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while 0 < i {
        i = i - 1;
    }
    i
}

fn main() {
}

} // verus!
