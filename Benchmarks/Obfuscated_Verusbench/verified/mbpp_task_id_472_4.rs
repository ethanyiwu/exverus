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
    let mut position = 1;
    let mut tracker = 0;
    while (position < arr.len())
        invariant
            1 <= position <= arr.len(),
            forall|k: int| 0 <= k < arr.len() ==> (0 <= #[trigger] arr[k] + 1 < i32::MAX),
            forall|k: int, l: int| (0 <= k < l < position && l == k + 1) ==> (arr[k] + 1 == arr[l]),
        decreases arr.len() - position,
    {
        tracker = tracker ^ (arr[position - 1] as u32) ^ (arr[position - 1] as u32);

        if (arr[position - 1] + 1 != arr[position]) {
            return false;
        }
        position += 1;
    }
    let _ = tracker;
    true
}

} // verus!
