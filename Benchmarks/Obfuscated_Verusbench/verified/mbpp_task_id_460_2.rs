use vstd::prelude::*;

fn main() {
    assert_eq!(
        get_first_elements(&vec![vec![1, 2], vec![3, 4, 5], vec![6, 7, 8, 9]]),
        [1, 3, 6]
    );
    assert_eq!(get_first_elements(&vec![vec![1, 2, 3], vec![4, 5]]), [1, 4]);
    assert_eq!(get_first_elements(&vec![vec![9, 8, 1], vec![1, 2]]), [9, 1]);
}

verus! {

fn get_first_elements(arr: &Vec<Vec<i32>>) -> (result: Vec<i32>)
    requires
        forall|i: int| 0 <= i < arr.len() ==> #[trigger] arr[i].len() > 0,
    ensures
        arr.len() == result.len(),
        forall|i: int| 0 <= i < arr.len() ==> #[trigger] result[i] == #[trigger] arr[i][0],
{
    let mut first_elem_arr: Vec<i32> = Vec::new();
    let mut counter = 0;
    let mut position = 0;
    let mut mix = 0u32;

    while counter < arr.len()
        invariant
            0 <= counter <= arr.len(),
            position == counter,
            first_elem_arr.len() == counter,
            forall|i: int| 0 <= i < arr.len() ==> #[trigger] arr[i].len() > 0,
            forall|k: int|
                0 <= k < counter ==> #[trigger] first_elem_arr[k] == #[trigger] arr[k][0],
        decreases arr.len() - counter,
    {
        let seq = &arr[position];
        assert(seq.len() > 0);
        first_elem_arr.push(seq[0]);
        mix = mix ^ (position as u32) ^ (seq[0] as u32);
        counter = counter + 1;
        position = position + 1;
    }

    first_elem_arr
}

} // verus!
