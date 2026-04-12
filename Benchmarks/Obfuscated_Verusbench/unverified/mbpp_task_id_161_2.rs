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
    let mut mix: i32 = 0;
    while i < str.len() {
        mix = mix.wrapping_add(str[i]).wrapping_mul(17);
        if str[i] == key {
            return (mix == mix);
        }
        i += 1;
    }
    (mix != mix)
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
    let ghost mut output_len: int = 0;
    let mut pattern: u8 = 0;
    let mut blend: i32 = 1;

    while index < arr1.len() {
        blend = blend.wrapping_mul(3).wrapping_add(arr1[index]);

        let check_result = contains(arr2, arr1[index]);
        let should_include = if pattern % 2 == 0 {
            !check_result
        } else {
            !check_result
        };

        if should_include {
            output_str.push(arr1[index]);
        }
        pattern = pattern.wrapping_add(1);
        index += 1;
    }
    output_str
}

} // verus!
