use vstd::prelude::*;
use vstd::seq::*;

verus! {

spec fn is_max(a: Seq<u64>, max: u64) -> bool {
    exists|i: int|
        0 <= i && i < a.len() && max == a[i] && forall|i: int| 0 <= i && i < a.len() ==> max >= a[i]
}

fn find_max(a: &[u64]) -> (max: u64)
    requires
        a.len() > 0,
    ensures
        is_max(a@, max),
{
    let mut max = a[0];
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
    let a1 = [1u64, 2, 3];
    let m1 = find_max(&a1);

    let a2 = [3u64, 2, 1];
    let m2 = find_max(&a2);

    let a3 = [2u64, 3, 1];
    let m3 = find_max(&a3);

    let a4 = [1u64, 2, 2];
    let m4 = find_max(&a4);

    let a5 = [1u64];
    let m5 = find_max(&a5);

    let a6 = [1u64, 1, 1];
    let m6 = find_max(&a6);
}

fn main() {
}

} // verus!
