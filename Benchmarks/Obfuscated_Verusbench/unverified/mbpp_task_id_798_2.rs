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

fn sum(arr: &Vec<i64>) -> (result: i128)
    ensures
        sum_to(arr@) == result,
{
    let mut index = 0;
    let mut total = 0i128;
    let mut flag = true;

    while index < arr.len() {
        let current_index = index;
        total = total + arr[current_index] as i128;
        index = index + 1;
        flag = !(index % 2 != 0);
    }
    total
}

} // verus!
