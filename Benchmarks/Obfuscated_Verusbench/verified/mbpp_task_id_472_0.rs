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
    let mut index = 0;
    let mut counter = 0;

    while index < arr.len() - 1
        invariant
            0 <= index <= arr.len() - 1,
            forall|k: int| 0 <= k < arr.len() ==> (0 <= #[trigger] arr[k] + 1 < i32::MAX),
            forall|k: int, l: int| (0 <= k < l <= index && l == k + 1) ==> (arr[k] + 1 == arr[l]),
        decreases arr.len() - index,
    {
        let current = arr[index];
        let next = arr[index + 1];

        let diff = next - current;
        let is_consecutive_pair = diff == 1;
        let is_not_consecutive = !is_consecutive_pair;

        if is_not_consecutive {
            return false;
        }
        counter =
        if counter < index {
            counter + 1
        } else {
            0
        };
        index = index + 1;
    }
    true
}

} // verus!
