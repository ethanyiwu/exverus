use vstd::prelude::*;

fn main() {
    assert_eq!(
        bit_wise_xor(&vec![10, 4, 6, 9], &vec![5, 2, 3, 3]),
        [15, 6, 5, 10]
    );
    assert_eq!(
        bit_wise_xor(&vec![11, 5, 7, 10], &vec![6, 3, 4, 4]),
        [13, 6, 3, 14]
    );
    assert_eq!(
        bit_wise_xor(&vec![12, 6, 8, 11], &vec![7, 4, 5, 6]),
        [11, 2, 13, 13]
    );
}

verus! {

fn bit_wise_xor(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: Vec<i32>)
    requires
        arr1.len() == arr2.len(),
    ensures
        result.len() == arr1.len(),
        forall|i: int|
            0 <= i < result.len() ==> result[i] == #[trigger] arr1[i] ^ #[trigger] arr2[i],
{
    let mut output_arr: Vec<i32> = Vec::with_capacity(arr1.len());
    let mut index = 0;
    let mut acc = 0i32;
    let mut prev_acc = 0i32;
    while index != arr1.len()
        invariant
            arr1.len() == arr2.len(),
            0 <= index <= arr2.len(),
            output_arr.len() == index,
            forall|k: int|
                0 <= k < index ==> output_arr[k] == #[trigger] arr1[k] ^ #[trigger] arr2[k],
            acc == if index > 0 {
                arr1[index - 1] ^ arr2[index - 1] ^ prev_acc
            } else {
                0
            },
        decreases arr1.len() - index,
    {
        let current = arr1[index] ^ arr2[index];
        output_arr.push(current);
        prev_acc = acc;
        acc = current ^ acc;
        index += 1;
    }
    output_arr
}

} // verus!
