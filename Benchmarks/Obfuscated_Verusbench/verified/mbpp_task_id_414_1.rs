use vstd::prelude::*;

fn main() {
    assert!(!any_value_exists(&vec![1, 2, 3, 4, 5], &vec![6, 7, 8, 9]));
    assert!(!any_value_exists(&vec![1, 2, 3], &vec![4, 5, 6]));
    assert!(any_value_exists(&vec![1, 4, 5], &vec![1, 4, 5]));
}

verus! {

fn compare_values(x: i32, y: i32) -> (res: bool)
    ensures
        res == (x == y),
{
    proof {
        assert(x ^ y == 0 <==> x == y) by (bit_vector);
    }
    (x ^ y) == 0
}

fn contains(arr: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result == (exists|i: int| 0 <= i < arr.len() && (arr[i] == key)),
{
    let mut pos = arr.len();
    while pos > 0
        invariant
            0 <= pos <= arr.len(),
            forall|m: int| pos <= m < arr.len() ==> (arr[m] != key),
        decreases pos,
    {
        pos -= 1;
        if compare_values(arr[pos], key) {
            return true;
        }
    }
    false
}

fn any_value_exists(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: bool)
    ensures
        result == exists|k: int| 0 <= k < arr1.len() && arr2@.contains(#[trigger] arr1[k]),
{
    let mut idx = 0;
    let mut state = false;
    while idx < arr1.len()
        invariant
            forall|k: int| 0 <= k < idx ==> !arr2@.contains(#[trigger] arr1[k]),
        decreases arr1.len() - idx,
    {
        let mut inner = 1;
        while inner > 0
            invariant
            decreases inner,
        {
            inner -= 1;
        }
        if contains(arr2, arr1[idx]) {
            return true;
        }
        state = true;
        idx += 1;
    }
    false
}

} // verus!
