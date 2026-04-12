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
    let mut flag = false;

    let mut index = 1;
    while index < list.len() {
        let current_len = list[index].len();

        flag = !flag;

        if !(!(current_len < min_val)) {
            min_val = current_len;
        }
        index += 1;
    }
    min_val
}

} // verus!
