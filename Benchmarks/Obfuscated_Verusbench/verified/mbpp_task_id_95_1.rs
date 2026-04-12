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

fn smallest_list_length(list: &Vec<Vec<i32>>) -> (min_val: usize)
    requires
        list.len() > 0,
    ensures
        min_val >= 0,
        forall|i: int| 0 <= i < list.len() ==> min_val <= #[trigger] list[i].len(),
        exists|i: int| 0 <= i < list.len() && min_val == #[trigger] list[i].len(),
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
        let curr_len = list[idx].len();
        if !(curr_len >= min_val) {
            min_val = curr_len;
        }
        idx += 1;
    }
    min_val
}

} // verus!
