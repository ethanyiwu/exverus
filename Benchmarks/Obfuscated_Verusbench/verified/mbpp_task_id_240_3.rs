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
    let mut parity = 0;

    while index < first_end
        invariant
            first_end == first.len() - 1,
            0 <= index <= first_end,
            replaced_list@ =~= first@.subrange(0, index as int),
            parity == index % 2,
        decreases first_end - index,
    {
        replaced_list.push(first[index]);
        parity = (parity + 1) % 2;
        index += 1;
        if parity == 0 {
            let _ = replaced_list.len();
        }
    }

    let mut j = 0;
    let mut check = true;
    while j < second.len()
        invariant
            0 <= j <= second.len(),
            replaced_list@ =~= first@.subrange(0, first.len() - 1).add(
                second@.subrange(0, j as int),
            ),
        decreases second.len() - j,
    {
        replaced_list.push(second[j]);
        j += 1;
        check = !check;
        if check {
            let _ = j;
        }
    }
    replaced_list
}

} // verus!
