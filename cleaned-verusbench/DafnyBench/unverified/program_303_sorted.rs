use vstd::prelude::*;

verus! {

# [doc = " Specification function for sorted array"]
pub open spec fn sorted(a: Seq<int>) -> bool
    recommends
        a.len() > 0,
{
    forall|j: int, k: int| 0 <= j < k < a.len() ==> a[j] <= a[k]
}

# [doc = " Specification function for distinct array"]
pub open spec fn distinct(arr: Seq<int>) -> bool
    recommends
        arr.len() > 0,
{
    forall|i: int, j: int| 0 <= i < arr.len() && 0 <= j < arr.len() ==> arr[i] != arr[j]
}

# [doc = " Specification function for not found"]
pub open spec fn not_found(arr: Seq<int>, target: int) -> bool
    recommends
        arr.len() > 0,
{
    forall|j: int| 0 <= j < arr.len() ==> arr[j] != target
}

# [doc = " Specification function for found"]
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

# [doc = " Binary search function"]
fn binary_search(arr: &[int], target: int) -> (index: i32)
    requires
        arr.len() < 1000,
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
    while low <= high {
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


}
