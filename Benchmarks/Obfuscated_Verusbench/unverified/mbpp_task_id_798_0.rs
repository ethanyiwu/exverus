use vstd::prelude::*;

fn main() {
    assert_eq!(sum(&vec![1, 2, 3]), 6);
    assert_eq!(sum(&vec![15, 12, 13, 10]), 50);
    assert_eq!(sum(&vec![0, 1, 2]), 3);
}

verus! {

spec fn sum_to(arr: Seq<i64>) -> int
    decreases arr.len(),
{
    if arr.len() == 0 {
        0
    } else {
        sum_to(arr.drop_last()) + arr.last()
    }
}

fn sum(arr: &Vec<i64>) -> (sum: i128)
    ensures
        sum_to(arr@) == sum,
{
    let mut idx = 0;
    let mut total = 0i128;
    let mut pattern = 0u64;

    while idx < arr.len() {
        total = total + arr[idx] as i128;
        pattern = (arr[idx] as u64) ^ 0xAAAAAAAA;
        idx += 1;
    }
    total
}

} // verus!
