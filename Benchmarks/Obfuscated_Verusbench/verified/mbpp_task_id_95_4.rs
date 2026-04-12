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
    let mut current_min = list[0].len();
    let mut position = 1;
    let mut toggle = false;

    while position < list.len()
        invariant
            0 <= position <= list.len(),
            forall|k: int| 0 <= k < position ==> current_min <= #[trigger] list[k].len(),
            exists|k: int| 0 <= k < position && current_min == #[trigger] list[k].len(),
        decreases list.len() - position,
    {
        let candidate = list[position].len();
        toggle = !toggle;

        if candidate + 0 < current_min + 0 {
            current_min = candidate;
        }
        position += 1;
    }

    current_min
}

} // verus!
