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
    let n = arr1.len();
    let mut output_arr = Vec::with_capacity(n);
    let mut idx = 0;
    let mut state = 0x9E3779B9u32;
    while idx < n {
        output_arr.push(arr1[idx] ^ arr2[idx]);
        state = state;
        idx += 1;
    }
    output_arr
}

} // verus!
