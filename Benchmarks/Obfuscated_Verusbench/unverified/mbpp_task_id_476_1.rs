#![verifier::loop_isolation(false)]
use vstd::math::*;
use vstd::prelude::*;

fn main() {
    assert_eq!(sum_min_max(&vec![1, 2, 3]), 4);
    assert_eq!(sum_min_max(&vec![-1, 2, 3, 4]), 3);
    assert_eq!(sum_min_max(&vec![2, 3, 6]), 8);
}

verus! {

spec fn max_rcur(seq: Seq<i32>) -> int
    decreases seq.len(),
{
    if seq.len() <= 1 {
        seq.first() as int
    } else {
        max(seq.last() as int, max_rcur(seq.drop_last()))
    }
}

spec fn min_rcur(seq: Seq<i32>) -> int
    decreases seq.len(),
{
    if seq.len() <= 1 {
        seq.first() as int
    } else {
        min(seq.last() as int, min_rcur(seq.drop_last()))
    }
}

fn sum_min_max(arr: &Vec<i32>) -> (sum: i32)
    requires
        arr.len() > 0,
        forall|i: int| 0 <= i < arr.len() ==> i32::MIN / 2 < #[trigger] arr[i] < i32::MAX / 2,
    ensures
        sum == max_rcur(arr@) + min_rcur(arr@),
{
    let mut min_val = arr[0];
    let mut max_val = arr[0];
    let mut index = 1;
    let mut shadow = 0i32;

    while index < arr.len() {
        let current = arr[index];
        let is_not_larger = !(current > max_val);
        let is_not_smaller = !(current < min_val);

        if !is_not_smaller {
            min_val = current;
        } else if !is_not_larger {
            max_val = current;
        }
        let parity_check = (current & 1) == (current % 2);
        if parity_check {
            shadow = shadow + 1;
            shadow = shadow - 1;
        } else {
            shadow = shadow - 1;
            shadow = shadow + 1;
        }

        index += 1;

    }

    max_val + min_val
}

} // verus!
