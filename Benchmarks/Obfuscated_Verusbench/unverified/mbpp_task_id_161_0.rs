use vstd::prelude::*;

fn main() {
    assert_eq!(
        remove_elements(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10], &vec![2, 4, 6, 8]),
        [1, 3, 5, 7, 9, 10]
    );
    assert_eq!(
        remove_elements(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10], &vec![1, 3, 5, 7]),
        [2, 4, 6, 8, 9, 10]
    );
    assert_eq!(
        remove_elements(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10], &vec![5, 7]),
        [1, 2, 3, 4, 6, 8, 9, 10]
    );
}

verus! {

fn contains(str: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result <==> (exists|i: int| 0 <= i < str.len() && (str[i] == key)),
{
    let mut i = 0;
    while i < str.len() {
        if (str[i] == key) {
            return true;
        }
        i += 1;
    }
    false
}

fn remove_elements(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: Vec<i32>)
    ensures
        forall|i: int|
            0 <= i < result.len() ==> (arr1@.contains(#[trigger] result[i]) && !arr2@.contains(
                #[trigger] result[i],
            )),
        forall|i: int|
            0 <= i < arr1.len() ==> (arr2@.contains(#[trigger] arr1[i]) || result@.contains(
                #[trigger] arr1[i],
            )),
{
    let mut output_str = Vec::new();
    let mut index: usize = 0;
    let mut shadow: i32 = 0;
    let ghost mut output_len: int = 0;

    while index < arr1.len() {
        let val = arr1[index];
        let contains_result = contains(arr2, val);
        shadow = shadow.wrapping_add(1).wrapping_mul(3);

        if !contains_result {
            output_str.push(val);
        }
        index += 1;
    }
    output_str
}

} // verus!
