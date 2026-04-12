use vstd::prelude::*;

verus! {

/// Specification function for sorted array
spec fn sorted(a: Seq<i32>) -> bool {
    forall|i: int, j: int| 0 <= i && i < j && j < a.len() ==> a[i] <= a[j]
}

/// Function to check if an array is sorted
fn sorted_func(a: &[i32]) -> (b: bool)
    requires
        a.len() > 0,
        a.len() < 1000,
        forall|k: int, l: int| 0 <= k && k < a.len() && k < l ==> a[k] <= a[l],
    ensures
        b == sorted(a@),
{
    let mut i = 0;
    while i < a.len() - 1
        invariant
            0 <= i && i < a.len(),
        decreases a.len() - i,
    {
        if a[i] > a[i + 1] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn main() {
}

} // verus!
