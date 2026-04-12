use vstd::prelude::*;

verus! {

pub open spec fn equal(x: int, y: int) -> bool {
    x == y
}

fn add(x: i64, y: i64) -> (r: i64)
    requires
        x >= i64::MIN && x <= i64::MAX,
        y >= i64::MIN && y <= i64::MAX,
        x + y >= i64::MIN && x + y <= i64::MAX,
    ensures
        r == x + y,
{
    if x + y > i64::MAX {
        return i64::MAX;
    } else if x + y < i64::MIN {
        return i64::MIN;
    } else {
        let r: i64 = x + y;
        r
    }
}

fn multiply(x: i64, y: i64) -> (r: i64)
    requires
        x >= i64::MIN && x <= i64::MAX,
        y >= i64::MIN && y <= i64::MAX,
        x * y >= i64::MIN && x * y <= i64::MAX,
    ensures
        r == x * y,
{
    if x * y > i64::MAX {
        return i64::MAX;
    } else if x * y < i64::MIN {
        return i64::MIN;
    } else {
        let r: i64 = x * y;
        r
    }
}


}
