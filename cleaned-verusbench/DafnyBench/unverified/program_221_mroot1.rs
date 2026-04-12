use vstd::prelude::*;

verus! {

# [doc = " Finds the integer square root of a number using iteration."]
fn mroot1(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX,
    ensures
        r >= 0,
        r * r <= n,
        n < (r + 1) * (r + 1),
{
    let mut r: u64 = 0;
    if n > 0 {
        while (r + 1) * (r + 1) <= n && n > 0 {
            r = r + 1;
        }
        r
    } else {
        0
    }
}

# [doc = " Finds the integer square root of a number using iteration."]
fn mroot2(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX,
    ensures
        r >= 0,
        r * r <= n,
        n < (r + 1) * (r + 1),
{
    let mut r: u64 = n;
    if n > 0 {
        while n < r * r && n > 0 {
            r = r - 1;
        }
        r
    } else {
        0
    }
}

# [doc = " Finds the integer square root of a number using binary search."]
fn mroot3(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX,
    ensures
        r >= 0,
        r * r <= n,
        n < (r + 1) * (r + 1),
{
    let mut y: u64 = n + 1;
    let mut r: u64 = 0;
    if n > 0 {
        while y != r + 1 && n > 0 {
            let h: u64 = (r + y) / 2;
            if h * h <= n {
                r = h;
            } else {
                y = h;
            }
        }
        r
    } else {
        0
    }
}


}
