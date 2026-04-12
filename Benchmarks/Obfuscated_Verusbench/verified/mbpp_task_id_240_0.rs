use vstd::prelude::*;

fn main() {
    assert_eq!(
        replace_last_element(&vec![1, 3, 5, 7, 9, 10], &vec![2, 4, 6, 8]),
        [1, 3, 5, 7, 9, 2, 4, 6, 8]
    );
    assert_eq!(
        replace_last_element(&vec![1, 2, 3, 4, 5], &vec![5, 6, 7, 8]),
        [1, 2, 3, 4, 5, 6, 7, 8]
    );
    assert_eq!(
        replace_last_element(&vec![1, 2, 4, 6, 8], &vec![3, 5, 7, 9]),
        [1, 2, 4, 6, 3, 5, 7, 9]
    );
}

verus! {

fn replace_last_element(first: &Vec<i32>, second: &Vec<i32>) -> (replaced_list: Vec<i32>)
    requires
        first.len() > 0,
    ensures
        replaced_list@ == first@.subrange(0, first.len() - 1).add(second@),
{
    let mut replaced_list = Vec::new();
    let first_end = first.len() - 1;
    let mut pos = 0;
    let mut flip = 0u8;

    while pos < first_end
        invariant
            first_end == first.len() - 1,
            0 <= pos <= first_end,
            flip < 2,
            replaced_list@ =~= first@.subrange(0, pos as int),
        decreases first_end - pos,
    {
        replaced_list.push(first[pos]);
        pos += 1;
        flip = (flip + 1) % 2;
    }

    let mut idx = 0;
    let mut phase = 0;
    while idx < second.len()
        invariant
            0 <= idx <= second.len(),
            replaced_list@ =~= first@.subrange(0, first.len() - 1).add(
                second@.subrange(0, idx as int),
            ),
        decreases second.len() - idx,
    {
        replaced_list.push(second[idx]);
        idx += 1;
        phase = idx;
    }
    replaced_list
}

} // verus!
