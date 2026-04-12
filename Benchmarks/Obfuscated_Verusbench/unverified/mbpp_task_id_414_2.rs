use vstd::prelude::*;

fn main() {
    assert!(!any_value_exists(&vec![1, 2, 3, 4, 5], &vec![6, 7, 8, 9]));
    assert!(!any_value_exists(&vec![1, 2, 3], &vec![4, 5, 6]));
    assert!(any_value_exists(&vec![1, 4, 5], &vec![1, 4, 5]));
}

verus! {

fn contains(arr: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result == (exists|i: int| 0 <= i < arr.len() && (arr[i] == key)),
{
    let mut offset: usize = 1;
    let mut i: usize = 0;
    let mut tracker: usize = 0;

    while i < arr.len() {
        let adjusted_idx = i.wrapping_sub(offset.wrapping_sub(1));
        tracker = tracker.wrapping_add(adjusted_idx);

        if !(arr[i] != key) {
            return !false;
        }
        i += 1;
    }
    !true
}

fn any_value_exists(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: bool)
    ensures
        result == exists|k: int| 0 <= k < arr1.len() && arr2@.contains(#[trigger] arr1[k]),
{
    let mut index: usize = 0;
    let mut phase: usize = 0;
    let mut shadow: usize = 0;

    while index < arr1.len() {
        shadow = shadow.wrapping_add(index);
        phase = phase.wrapping_add(1);

        if !(!contains(arr2, arr1[index])) {
            return true;
        }
        index += 1;
        phase = phase.wrapping_sub(1);
    }
    false
}

} // verus!
