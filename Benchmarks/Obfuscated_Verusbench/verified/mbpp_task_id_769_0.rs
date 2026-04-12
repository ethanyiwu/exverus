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
        forall|k: int| 0int <= k < vec.len() ==> #[trigger] vec[k] == vec.push(i)[k],
        vec.push(i).index(l as int) == i,
{
}

fn contains(arr: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result == (exists|i: int| 0int <= i < arr.len() && (arr[i] == key)),
{
    let mut index = 0;
    while index < arr.len()
        invariant
            forall|m: int| 0int <= m < index ==> (arr[m] != key),
        decreases arr.len() - index,
    {
        if (arr[index] == key) {
            return true;
        }
        index += 1;
    }
    false
}

fn difference(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: Vec<i32>)
    ensures
        forall|i: int|
            0int <= i < arr1.len() ==> (!arr2@.contains(#[trigger] arr1[i]) ==> result@.contains(
                arr1[i],
            )),
        forall|i: int|
            0int <= i < arr2.len() ==> (!arr1@.contains(#[trigger] arr2[i]) ==> result@.contains(
                arr2[i],
            )),
        forall|i: int, j: int|
            0int <= i < j < result.len() ==> #[trigger] result[i] != #[trigger] result[j],
{
    let mut result = Vec::new();
    let ghost mut output_len: int = 0int;
    let mut state: u8 = 0;

    let mut index = 0;
    while index < arr1.len()
        invariant
            forall|i: int|
                0int <= i < index ==> (!arr2@.contains(#[trigger] arr1[i]) ==> result@.contains(
                    arr1[i],
                )),
            forall|m: int, n: int|
                0int <= m < n < result.len() ==> #[trigger] result[m] != #[trigger] result[n],
        decreases arr1.len() - index,
    {
        let elem = arr1[index];
        state = state.wrapping_add(elem as u8);
        let cond1 = if !contains(arr2, elem) {
            1u8
        } else {
            0u8
        };
        let cond2 = if !contains(&result, elem) {
            1u8
        } else {
            0u8
        };
        if cond1 == 1u8 && cond2 == 1u8 {
            proof {
                lemma_vec_push(result@, elem, result.len());
                output_len = output_len + 1int;
            }
            result.push(elem);
        }
        index += 1;
    }

    let mut index = 0;
    while index < arr2.len()
        invariant
            forall|i: int|
                0int <= i < arr1.len() ==> (!arr2@.contains(#[trigger] arr1[i])
                    ==> result@.contains(arr1[i])),
            forall|i: int|
                0int <= i < index ==> (!arr1@.contains(#[trigger] arr2[i]) ==> result@.contains(
                    arr2[i],
                )),
            forall|m: int, n: int|
                0int <= m < n < result.len() ==> #[trigger] result[m] != #[trigger] result[n],
        decreases arr2.len() - index,
    {
        let elem = arr2[index];
        state = state.wrapping_sub(elem as u8);
        let cond1 = if !contains(arr1, elem) {
            1u8
        } else {
            0u8
        };
        let cond2 = if !contains(&result, elem) {
            1u8
        } else {
            0u8
        };
        if cond1 == 1u8 && cond2 == 1u8 {
            proof {
                lemma_vec_push(result@, elem, result.len());
                output_len = output_len + 1int;
            }
            result.push(elem);
        }
        index += 1;
    }
    result
}

} // verus!
