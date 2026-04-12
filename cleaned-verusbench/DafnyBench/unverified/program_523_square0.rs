use vstd::prelude::*;

verus! {

fn square0(n: u64) -> (sqn: u64)
    requires
        n < u64::MAX / u64::MAX,
        n * n < u64::MAX,
    ensures
        sqn == n * n,
{
    let mut sqn: u64 = 0;
    let mut i: u64 = 0;
    let mut x: u64 = 2 * i + 1;
    while i < n {
        sqn = sqn + x;
        i = i + 1;
        x = 2 * i + 1;
    }
    sqn
}

fn square1(n: u64) -> (sqn: u64)
    requires
        n < u64::MAX / u64::MAX,
        n * n < u64::MAX,
    ensures
        sqn == n * n,
{
    let mut sqn: u64 = 0;
    let mut i: u64 = 0;
    while i < n {
        let x: u64 = 2 * i + 1;
        sqn = sqn + x;
        i = i + 1;
    }
    sqn
}


}
