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
    let mut pos: usize = 0;
    let mut found: bool = false;
    while pos < arr.len() {
        if arr[pos] == key {
            found = true;
            return true;
        }
        pos += 1;
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
    while index < arr1.len() {
        let current_val = arr1[index];
        let in_other = contains(arr2, current_val);
        let in_result = contains(&result, current_val);

        let arithmetic_check = (in_other as i32) + (in_result as i32) == 0;

        if arithmetic_check {
            result.push(current_val);
        }
        index += 1;
    }

    let mut index = 0;
    while index < arr2.len() {
        let current_val = arr2[index];
        let in_other = contains(arr1, current_val);
        let in_result = contains(&result, current_val);

        let arithmetic_check = (in_other as i32) + (in_result as i32) == 0;

        if arithmetic_check {
            result.push(current_val);
        }
        index += 1;
    }
    result
}

} // verus!
