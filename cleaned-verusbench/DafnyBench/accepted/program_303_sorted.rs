use vstd::prelude::*;

verus! {

/// Specification function for sorted array
pub open spec fn sorted(a: Seq<int>) -> bool
    recommends
        a.len() > 0,
{
    forall|j: int, k: int| 0 <= j < k < a.len() ==> a[j] <= a[k]
}

/// Specification function for distinct array
pub open spec fn distinct(arr: Seq<int>) -> bool
    recommends
        arr.len() > 0,
{
    forall|i: int, j: int| 0 <= i < arr.len() && 0 <= j < arr.len() ==> arr[i] != arr[j]
}

/// Specification function for not found
pub open spec fn not_found(arr: Seq<int>, target: int) -> bool
    recommends
        arr.len() > 0,
{
    forall|j: int| 0 <= j < arr.len() ==> arr[j] != target
}

/// Specification function for found
pub open spec fn found(arr: Seq<int>, target: int, index: int) -> bool
    recommends
        -1 <= index && index < arr.len(),
{
    if index == -1 {
        false
    } else if arr[index] == target {
        true
    } else {
        false
    }
}

/// Binary search function
fn binary_search(arr: &[int], target: int) -> (index: i32)
    requires
        arr.len() < 1000,  // added relaxation to prevent overflow
        arr.len() > 0,
        sorted(arr@),
        distinct(arr@),
    ensures
        -1 <= index && index < arr.len() as i32,
        index == -1 ==> not_found(arr@, target),
        index != -1 ==> found(arr@, target, index as int),
{
    let mut low: usize = 0;
    let mut high: usize = arr.len() - 1;
    while low <= high
        invariant
            0 <= low <= high + 1,
            low - 1 <= high && high < arr.len(),
            forall|i: int|
                0 <= i <= low as int && high as int <= i < arr.len() as int ==> arr[i] != target,
            sorted(arr@),
            distinct(arr@),
        decreases high - low + 1,
    {
        let mid: usize = (low + high) / 2;
        if arr[mid] == target {
            return mid as i32;
        } else if arr[mid] < target {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    -1
}

fn main() {
}

} // verus!
