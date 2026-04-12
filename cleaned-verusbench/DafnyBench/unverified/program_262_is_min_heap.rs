use vstd::prelude::*;

verus! {

# [doc = " Specification function to check if a state is a min heap"]
spec fn is_min_heap(a: Seq<int>) -> bool
    recommends
        a.len() >= 0,
{
    &&& 0 < a.len() / 2 ==> a[0] <= a[1]
    &&& forall|i: int, j: int| 0 <= i && i < a.len() / 2 && j == 2 * i + 1 ==> a[i] <= a[j]
    &&& forall|i: int, j: int|
        0 <= i && i < a.len() / 2 && 2 * i + 2 < a.len() && j == 2 * i + 2 ==> a[i] <= a[j]
}

# [doc = " Proof function to add two numbers"]
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

# [doc = " Proof function to multiply two numbers"]
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
