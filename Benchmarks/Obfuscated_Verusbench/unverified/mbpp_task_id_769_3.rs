use vstd::prelude::*;

fn main() {
    assert_eq!(
        difference(&vec![10, 15, 20, 25, 30, 35, 40], &vec![25, 40, 35]),
        [10, 15, 20, 30]
    );
    assert_eq!(
        difference(&vec![1, 2, 3, 4, 5], &vec![6, 7, 1]),
        [2, 3, 4, 5, 6, 7]
    );
    assert_eq!(difference(&vec![1, 2, 3], &vec![6, 7, 1]), [2, 3, 6, 7]);
}

verus! {

fn contains(arr: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result == (exists|i: int| 0 <= i < arr.len() && (arr[i] == key)),
{
    let mut index = 0;
    while index < arr.len() {
        if arr[index] == key {
            return true;
        }
        index += 1;
    }
    false
}

fn difference(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: Vec<i32>)
    ensures
        forall|i: int|
            0 <= i < arr1.len() ==> (!arr2@.contains(#[trigger] arr1[i]) ==> result@.contains(
                arr1[i],
            )),
        forall|i: int|
            0 <= i < arr2.len() ==> (!arr1@.contains(#[trigger] arr2[i]) ==> result@.contains(
                arr2[i],
            )),
        forall|i: int, j: int|
            0 <= i < j < result.len() ==> #[trigger] result[i] != #[trigger] result[j],
{
    let mut result = Vec::new();
    let ghost mut output_len: int = 0;

    let mut index = 0;
    let mut alt = false;
    while index < arr1.len() {
        let elem = arr1[index];
        let in_arr2 = contains(arr2, elem);
        let in_result = contains(&result, elem);
        let should_add = !in_arr2 && !in_result;
        if should_add {
            result.push(elem);
        }
        index += 1;
        alt = !alt;
    }

    index = 0;
    alt = true;
    while index < arr2.len() {
        let elem = arr2[index];
        let in_arr1 = contains(arr1, elem);
        let in_result = contains(&result, elem);
        let should_add = !in_arr1 && !in_result;
        if should_add {
            result.push(elem);
        }
        index += 1;
        alt = !alt;
    }
    result
}

} // verus!
