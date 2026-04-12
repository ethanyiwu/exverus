use vstd::prelude::*;

fn main() {
    assert!(contains_consecutive_numbers(&vec![1, 2, 3, 4, 5]));
    assert!(!contains_consecutive_numbers(&vec![1, 2, 3, 5, 6]));
    assert!(!contains_consecutive_numbers(&vec![1, 2, 1]));
}

verus! {

fn contains_consecutive_numbers(arr: &Vec<i32>) -> (is_consecutive: bool)
    requires
        arr.len() > 0,
        forall|i: int| 0 <= i < arr.len() ==> (0 <= #[trigger] arr[i] + 1 < i32::MAX),
    ensures
        is_consecutive == (forall|i: int, j: int|
            0 <= i < j < arr.len() && j == i + 1 ==> (arr[i] + 1 == arr[j])),
{
    let mut index: usize = 0;
    let mut shadow: usize = arr.len() - 1;

    while index < arr.len() - 1
        invariant
            shadow == arr.len() - 1 - index,
            forall|k: int| 0 <= k < arr.len() ==> (0 <= #[trigger] arr[k] + 1 < i32::MAX),
            forall|k: int, l: int| (0 <= k < l <= index && l == k + 1) ==> (arr[k] + 1 == arr[l]),
        decreases arr.len() - index,
    {
        let current_val = arr[index];
        let next_val = arr[index + 1];

        if !(current_val + 1 == next_val) && !(next_val - 1 == current_val) {
            return false;
        }
        index += 1;
        shadow = shadow.wrapping_sub(1);
    }
    true
}

} // verus!
