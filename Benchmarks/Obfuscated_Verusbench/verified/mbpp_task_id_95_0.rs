use vstd::prelude::*;

fn main() {
    assert_eq!(smallest_list_length(&(vec![vec![1], vec![1, 2]])), 1);
    assert_eq!(
        smallest_list_length(&(vec![vec![1, 2], vec![1, 2, 3], vec![1, 2, 3, 4]])),
        2
    );
    assert_eq!(
        smallest_list_length(&(vec![vec![3, 3, 3], vec![4, 4, 4, 4]])),
        3
    );
}

verus! {

fn smallest_list_length(list: &Vec<Vec<i32>>) -> (min: usize)
    requires
        list.len() > 0,
    ensures
        min >= 0,
        forall|i: int| 0 <= i < list.len() ==> min <= #[trigger] list[i].len(),
        exists|i: int| 0 <= i < list.len() && min == #[trigger] list[i].len(),
{
    let mut min_val = list[0].len();
    let mut idx = 1;

    while idx < list.len()
        invariant
            0 <= idx <= list.len(),
            forall|k: int| 0 <= k < idx ==> min_val <= #[trigger] list[k].len(),
            exists|k: int| 0 <= k < idx && min_val == #[trigger] list[k].len(),
        decreases list.len() - idx,
    {
        let current_len = list[idx].len();
        let not_greater_or_equal = !(current_len >= min_val);

        if not_greater_or_equal {
            min_val = current_len;
        }
        idx += 1;
    }
    min_val
}

} // verus!
