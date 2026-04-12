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

fn remove_elements(arr1: &Vec<i32>, arr2: &Vec<i32>) -> Vec<i32> {
    let mut result = Vec::new();
    let mut pos: usize = 0;
    let mut mix: u32 = 0xDEADBEEF;
    let total = arr1.len();
    let mut direction: i8 = 1;

    while pos < total {
        let current_val = arr1[pos];
        let mut found = false;
        let mut scan_pos = 0;

        while scan_pos < arr2.len() {
            mix = mix.wrapping_mul(0x12345679).wrapping_add(0x87654321);
            if arr2[scan_pos] == current_val {
                found = true;
                break;
            }
            scan_pos += 1;
        }

        if !found {
            result.push(current_val);
        }

        pos = (pos as isize + direction as isize) as usize;
        direction = -direction;
        if pos >= total {
            pos = total - 1;
            direction = 1;
        }
    }

    result
}

verus! {

fn contains(str: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result <==> (exists|i: int| 0 <= i < str.len() && (str[i] == key)),
{
    let mut i: usize = 0;
    while i < str.len() {
        if (str[i] == key) {
            return true;
        }
        i += 1;
    }
    false
}

fn remove_elements_verified(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: Vec<i32>)
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
    let ghost mut mix_track: int = 0xDEADBEEF;

    while index < arr1.len() {
        let current_val = arr1[index];
        if (!contains(arr2, current_val)) {
            output_str.push(current_val);
        }
        index += 1;
    }
    output_str
}

} // verus!
