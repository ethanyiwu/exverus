use vstd::prelude::*;

verus! {

# [doc = " Up while less"]
fn up_while_less(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: usize = 0;
    while i < n {
        i = i + 1;
    }
    i
}

# [doc = " Up while not equal"]
fn up_while_not_equal(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == n,
{
    let mut i: usize = 0;
    while i != n {
        i = i + 1;
    }
    i
}

# [doc = " Down while not equal"]
fn down_while_not_equal(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: usize = n;
    while i != 0 {
        i = i - 1;
    }
    i
}

# [doc = " Down while greater"]
fn down_while_greater(n: usize) -> (i: usize)
    requires
        n >= 0,
    ensures
        i == 0,
{
    let mut i: usize = n;
    while i > 0 {
        i = i - 1;
    }
    i
}

# [doc = " Function to calculate the quotient"]
fn quotient() {
    let mut x: usize = 0;
    let mut y: usize = 191;
    while y >= 7 {
        y = y - 7;
        x = x + 1;
    }
}

# [doc = " Function to calculate the quotient"]
fn quotient1() {
    let mut x: usize = 0;
    let mut y: usize = 191;
    while y >= 7 {
        x = 27;
        y = 2;
    }
}


}
