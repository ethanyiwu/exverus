use vstd::prelude::*;

verus! {

/// Specification function to check if an array is sorted
spec fn sorted(a: Seq<int>) -> bool {
    forall|j: int, k: int| 0 <= j < k < a.len() ==> a[j] <= a[k]
}

/// Specification function to check if an array is distinct
spec fn distinct(arr: Seq<int>) -> bool {
    forall|i: int, j: int| 0 <= i < arr.len() && 0 <= j < arr.len() ==> i == j ==> arr[i] != arr[j]
}

/// Specification function to check if a target is not found in an array
spec fn not_found(arr: Seq<int>, target: int) -> bool {
    forall|j: int| 0 <= j < arr.len() ==> arr[j] != target
}

/// Specification function to check if a target is found in an array
spec fn found(arr: Seq<int>, target: int, index: int) -> bool
    recommends
        -1 <= index && index < arr.len(),
{
    if index == -1 {
        false
    } else {
        arr[index] == target
    }
}

/// Function to perform binary search
fn binary_search(arr: &[int], target: int) -> (index: i32)
    requires
        distinct(arr@),
        sorted(arr@),
        arr.len() < 100000,  // added relaxation to prevent overflow

    ensures
        -1 <= index && index < arr.len() as i32,
        index == -1 ==> not_found(arr@, target),
        index != -1 ==> found(arr@, target, index as int),
{
    if arr.len() == 0 {
        -1
    } else {
        let mut low = 0;
        let mut high = arr.len() - 1;
        while low <= high
            invariant
                low - 1 <= high && high < arr.len(),
                distinct(arr@),

            decreases low - high,
        {
            let mid = (low + high) / 2;
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

fn main() {
}

} // verus!
