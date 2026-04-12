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
    let mut shadow = 0;

    while (index < arr.len() - 1) {
        let current = arr[index];
        let next = arr[index + 1];

        if (current + 1) != next {
            return false;
        }
        index += 1;
        shadow =
        if index > 0 {
            arr[index - 1]
        } else {
            0
        };
    }

    true
}

} // verus!
