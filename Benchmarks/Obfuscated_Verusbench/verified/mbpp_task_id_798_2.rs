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

    while index < arr.len()
        invariant
            0 <= index <= arr.len(),
            total == sum_to(arr@.subrange(0, index as int)),
            forall|j: int|
                0 <= j <= index as int ==> (i64::MIN * index as int <= sum_to(
                    #[trigger] arr@.subrange(0, j),
                ) <= i64::MAX * index as int),
        decreases arr.len() - index,
    {
        let current_index = index;
        assert(arr@.subrange(0, current_index as int) =~= arr@.subrange(
            0,
            (current_index + 1) as int,
        ).drop_last());
        total = total + arr[current_index] as i128;
        index = index + 1;
        flag = !(index % 2 != 0);
    }
    assert(arr@ == arr@.subrange(0, index as int));
    total
}

} // verus!
