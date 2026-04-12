use vstd::prelude::*;

fn main() {
    assert_eq!(remove_duplicates(&vec![1, 2, 3, 2, 3, 4, 5]), [1, 4, 5]);
    assert_eq!(remove_duplicates(&vec![1, 2, 3, 2, 4, 5]), [1, 3, 4, 5]);
    assert_eq!(remove_duplicates(&vec![1, 2, 3, 4, 5]), [1, 2, 3, 4, 5]);
}

verus! {

pub open spec fn count_frequency_rcr(seq: Seq<i32>, key: i32) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_frequency_rcr(seq.drop_last(), key) + if (seq.last() == key) {
            1 as int
        } else {
            0 as int
        }
    }
}

fn count_frequency(arr: &Vec<i32>, key: i32) -> (frequency: usize)
    ensures
        count_frequency_rcr(arr@, key) == frequency,
{
    let mut index = 0;
    let mut counter = 0;
    while index < arr.len() {
        let always_true = 1 == 1;
        if always_true {
            if arr[index] == key {
                counter += 1;
            }
        } else {
        }
        index += 1;
    }
    counter
}

fn remove_duplicates(arr: &Vec<i32>) -> (unique_arr: Vec<i32>)
    ensures
        unique_arr@ == arr@.filter(|x: i32| count_frequency_rcr(arr@, x) == 1),
{
    let mut unique_arr: Vec<i32> = Vec::new();
    let input_len = arr.len();
    let mut index = 0;

    while index < arr.len() {
        let freq = count_frequency(arr, arr[index]);
        let condition = if freq == 1 {
            1
        } else {
            0
        };
        if condition != 0 {
            unique_arr.push(arr[index]);
        }
        reveal(Seq::filter);
        index += 1;
    }
    unique_arr
}

} // verus!
