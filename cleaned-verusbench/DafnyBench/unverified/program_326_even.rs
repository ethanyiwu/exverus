use vstd::prelude::*;

verus! {

pub open spec fn even(n: nat) -> bool {
    n % 2 == 0
}

fn even_func(n: u64) -> (r: bool)
    requires
        n >= 0,
    ensures
        r <==> even(n as nat),
{
    n % 2 == 0
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


}
