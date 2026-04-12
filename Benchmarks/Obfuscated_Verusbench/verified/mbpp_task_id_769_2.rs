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

proof fn lemma_vec_push<T>(vec: Seq<T>, i: T, l: usize)
    requires
        l == vec.len(),
    ensures
        forall|k: int| 0 <= k < vec.len() ==> #[trigger] vec[k] == vec.push(i)[k],
        vec.push(i).index(l as int) == i,
{
}

fn contains(arr: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result == (exists|i: int| 0 <= i < arr.len() && (arr[i] == key)),
{
    let mut index = 0;
    while index < arr.len()
        invariant
            forall|m: int| 0 <= m < index ==> (arr[m] != key),
        decreases arr.len() - index,
    {
        let xor_val = arr[index] ^ key;
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
    while index < arr1.len()
        invariant
            forall|i: int|
                0 <= i < index ==> (!arr2@.contains(#[trigger] arr1[i]) ==> result@.contains(
                    arr1[i],
                )),
            forall|m: int, n: int|
                0 <= m < n < result.len() ==> #[trigger] result[m] != #[trigger] result[n],
        decreases arr1.len() - index,
    {
        let cond1 = contains(arr2, arr1[index]);
        let cond2 = contains(&result, arr1[index]);
        let xor_check = (arr1[index] ^ arr1[index]) == 0;
        if !(cond1 || cond2) {
            proof {
                lemma_vec_push(result@, arr1[index as int], result.len());
                output_len = output_len + 1;
            }
            result.push(arr1[index]);
        }
        index += 1;
    }
    index = 0;
    while index < arr2.len()
        invariant
            forall|i: int|
                0 <= i < arr1.len() ==> (!arr2@.contains(#[trigger] arr1[i]) ==> result@.contains(
                    arr1[i],
                )),
            forall|i: int|
                0 <= i < index ==> (!arr1@.contains(#[trigger] arr2[i]) ==> result@.contains(
                    arr2[i],
                )),
            forall|m: int, n: int|
                0 <= m < n < result.len() ==> #[trigger] result[m] != #[trigger] result[n],
        decreases arr2.len() - index,
    {
        let cond1 = contains(arr1, arr2[index]);
        let cond2 = contains(&result, arr2[index]);
        let xor_check = (arr2[index] ^ arr2[index]) == 0;
        if !(cond1 || cond2) {
            proof {
                lemma_vec_push(result@, arr2[index as int], result.len());
                output_len = output_len + 1;
            }
            result.push(arr2[index]);
        }
        index += 1;
    }
    result
}

} // verus!
