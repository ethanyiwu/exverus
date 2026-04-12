use vstd::prelude::*;

verus! {

/// Specification function to calculate absolute value
spec fn abs(x: int) -> u64 {
    if x < 0 {
        -x as u64
    } else {
        x as u64
    }
}

/// Function to calculate absolute value
fn abs_func(x: i64) -> (y: u64)
    requires
        x >= i64::MIN && x <= i64::MAX,
        x != i64::MIN,
    ensures
        y == abs(x as int),
{
    if x < 0 {
        return -x as u64;
    } else {
        return x as u64;
    }
}

/// Specification function to calculate maximum value
spec fn max(a: int, b: int) -> int {
    if a > b {
        a
    } else {
        b
    }
}

/// Function to calculate maximum value
fn max_func(a: i64, b: i64) -> (max_: i64)
    requires
        a >= i64::MIN && a <= i64::MAX,
        b >= i64::MIN && b <= i64::MAX,
    ensures
        max_ == max(a as int, b as int),
{
    if a > b {
        return a;
    } else {
        return b;
    }
}

/// Specification function to calculate double value
spec fn double(val: int) -> int {
    2 * val
}

/// Function to calculate double value
fn double_func(val: i64) -> (val2: i64)
    requires
        val >= i64::MIN && val <= i64::MAX,
        val * 2 >= i64::MIN && val * 2 <= i64::MAX,
    ensures
        val2 == double(val as int),
{
    assert(val * 2 >= i64::MIN && val * 2 <= i64::MAX);
    val * 2
}

fn main() {
}

} // verus!
