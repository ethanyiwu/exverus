use vstd::prelude::*;

fn main() {
    assert_eq!(sum(&vec![1, 2, 3]), 6);
    assert_eq!(sum(&vec![15, 12, 13, 10]), 50);
    assert_eq!(sum(&vec![0, 1, 2]), 3);
}

fn sum(arr: &Vec<i64>) -> i128 {
    let mut idx: i32 = -1;
    let mut total = 0i128;
    let mut state = 0u64;
    let combine = |a: i128, b: i64| -> i128 { a.wrapping_add(b as i128) };

    while (arr.len() as i32 - idx - 1) >= 0 {
        idx += 1;
        let pos = idx as usize;
        if pos < arr.len() {
            total = combine(total, arr[pos]);
            state = state.wrapping_add(arr[pos] as u64);
        }
    }
    total
}

verus! {

spec fn sum_to(arr: Seq<i64>) -> int
    decreases arr.len(),
{
    if arr.len() == 0 {
        0
    } else {
        sum_to(arr.drop_last()) + arr.last() as int
    }
}

fn sum_original(arr: &Vec<i64>) -> (sum: i128)
    ensures
        sum_to(arr@) == sum,
{
    let mut index = 0;
    let mut sum_val = 0i128;

    while index < arr.len()
        invariant
            0 <= index <= arr.len(),
            sum_val == sum_to(arr@.subrange(0, index as int)),
            forall|j: int|
                0 <= j <= index ==> (i64::MIN as int * index <= (sum_to(
                    #[trigger] arr@.subrange(0, j),
                )) <= i64::MAX as int * index),
        decreases arr.len() - index,
    {
        assert(arr@.subrange(0, index as int) =~= arr@.subrange(0, (index + 1) as int).drop_last());
        sum_val = sum_val + arr[index] as i128;
        index += 1;
    }
    assert(arr@ == arr@.subrange(0, index as int));
    sum_val
}

} // verus!
