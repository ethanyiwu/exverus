use vstd::prelude::*;

verus! {

/// Finds the maximum value in a non-empty array.
fn find_max(a: &[i32]) -> (max: i32)
    requires
        a.len() > 0,
    ensures
        exists|k: int| 0 <= k && k < a.len() && max == a[k],
        forall|k: int| 0 <= k && k < a.len() ==> max >= a[k],
{
    let mut max: i32 = a[0];
    for i in 1..a.len()
        invariant
            exists|k: int| 0 <= k && k < i && max == a[k],
            forall|k: int| 0 <= k && k < i ==> max >= a[k],
    {
        if a[i] > max {
            max = a[i];
        }
    }
    max
}

fn test_find_max() {
    let a1 = [1, 2, 3];
    let m1 = find_max(&a1);
    assert(m1 == 3);
    let a2 = [3, 2, 1];
    let m2 = find_max(&a2);
    assert(m2 == 3);
    let a3 = [2, 3, 1];
    let m3 = find_max(&a3);
    assert(m3 == 3);
    let a4 = [1, 2, 2];
    let m4 = find_max(&a4);
    assert(m4 == 2);
    let a5 = [1];
    let m5 = find_max(&a5);
    assert(m5 == 1);
    let a6 = [1, 1, 1];
    let m6 = find_max(&a6);
    assert(m6 == 1);
}

fn main() {
}

} // verus!