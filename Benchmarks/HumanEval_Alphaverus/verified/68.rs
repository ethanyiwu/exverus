use vstd::prelude::*;

verus! {

fn monotonic(l: Vec<i32>) -> (ret: bool)
    ensures
        ret <==> (forall|i: int, j: int| 0 <= i < j < l@.len() ==> l@.index(i) <= l@.index(j)) || (
        forall|i: int, j: int| 0 <= i < j < l@.len() ==> l@.index(i) >= l@.index(j)),
{
    if l.len() == 0 || l.len() == 1 {
        return true;
    }
    let mut increasing = true;
    let mut decreasing = true;

    let mut n = 0;
    while n < l.len() - 1
        invariant
            n <= l.len() - 1,
            increasing <==> forall|i: int, j: int|
                0 <= i < j < n + 1 ==> l@.index(i) <= l@.index(j),
            decreasing <==> forall|i: int, j: int|
                0 <= i < j < n + 1 ==> l@.index(i) >= l@.index(j),
        decreases l.len() - n,
    {
        if l[n] < l[n + 1] {
            decreasing = false;
        } else if l[n] > l[n + 1] {
            increasing = false;
        }
        n += 1;
    }
    increasing || decreasing
}

} // verus!
fn main() {}
