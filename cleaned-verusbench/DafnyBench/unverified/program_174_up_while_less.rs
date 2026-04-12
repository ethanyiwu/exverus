use vstd::prelude::*;

verus! {

fn up_while_less(n: u64) -> (i: u64)
    requires
        n as int >= 0,
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
        n as int >= 0,
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
        n as int >= 0,
    ensures
        i == 0,
{
    let mut i: u64 = n;
    while i != 0 {
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
    while 0 < i {
        i = i - 1;
    }
    i
}

fn quotient() {
    let mut x: u64 = 0;
    let mut y: u64 = 191;
    while 7 <= y {
        y = y - 7;
        x = x + 1;
    }
}

fn quotient1() {
    let mut x: u64 = 0;
    let mut y: u64 = 191;
    while 7 <= y {
        x = 27;
        y = 2;
    }
}


}
