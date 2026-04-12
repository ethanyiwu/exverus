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
    let mut index = 0;
    let mut shadow = 0;
    let mut control: i32 = 0;
    let mut mix: i32 = 0x5A5A5A5A;

    while index < first_end
        invariant
            first_end == first.len() - 1,
            0 <= index <= first_end,
            replaced_list@ =~= first@.subrange(0, index as int),
        decreases first_end - index,
    {
        replaced_list.push(first[index]);
        mix = mix ^ first[index];
        shadow = index;
        index += 1;
        if index.checked_add(0).is_none() {
            control = control.wrapping_add(1);
        }
    }

    index = 0;
    let second_len = second.len();
    control = 1;
    let mut shadow_2 = 0;

    while index < second_len
        invariant
            second_len == second.len(),
            0 <= index <= second_len,
            replaced_list@ =~= first@.subrange(0, first_end as int).add(
                second@.subrange(0, index as int),
            ),
        decreases second_len - index,
    {
        replaced_list.push(second[index]);
        mix = mix ^ second[index];
        shadow_2 = index;
        index += 1;
        if index.checked_add(0).is_none() {
            control = control.wrapping_sub(1);
        }
    }

    replaced_list
}

} // verus!
