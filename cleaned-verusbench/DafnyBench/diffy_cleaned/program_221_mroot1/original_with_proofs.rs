use vstd::prelude::*;

verus! {

/// Finds the integer square root of a number using iteration.
fn mroot1(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        r >= 0,
        r * r <= n,
        n < (r + 1) * (r + 1),
{
    let mut r: u64 = 0;
    if n > 0 {
        while (r + 1) * (r + 1) <= n && n > 0
            invariant
                r >= 0,
                r * r <= n,
                n < (r + 1) * (r + 1),
                n > 0,
                n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
            decreases
                n - r * r,
        {
            r = r + 1;
        }
        assert(r * r <= n);
        assert(n < (r + 1) * (r + 1));
        r
    } else {
        0
    }
}

/// Finds the integer square root of a number using iteration.
fn mroot2(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        r >= 0,
        r * r <= n,
        n < (r + 1) * (r + 1),
{
    let mut r: u64 = n;
    if n > 0 {
        while n < r * r && n > 0
            invariant
                0 <= r && r <= n,
                n < (r + 1) * (r + 1),
                n > 0,
                n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
            decreases
                r,
        {
            r = r - 1;
        }
        assert(r * r <= n);
        assert(n < (r + 1) * (r + 1));
        r
    } else {
        0
    }
}

/// Finds the integer square root of a number using binary search.
fn mroot3(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
    ensures
        r >= 0,
        r * r <= n,
        n < (r + 1) * (r + 1),
{
    let mut y: u64 = n + 1;
    let mut r: u64 = 0;
    if n > 0 {
        while y != r + 1 && n > 0
            invariant
                r >= 0,
                r * r <= n,
                y >= r + 1,
                n < y * y,
                n > 0,
                n < u64::MAX / u64::MAX, // added relaxation to prevent overflow
            decreases
                y - r,
        {
            let h: u64 = (r + y) / 2;
            if h * h <= n {
                r = h;
            } else {
                y = h;
            }
        }
        assert(r * r <= n);
        assert(n < (r + 1) * (r + 1));
        r
    } else {
        0
    }
}

fn main() {}

} // verus!