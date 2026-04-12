use vstd::prelude::*;

fn main() {
    assert!(!is_sub_array(&vec![1, 4, 3, 5], &vec![1, 2]));
    assert!(is_sub_array(&vec![1, 2, 1], &vec![1, 2, 1]));
    assert!(!is_sub_array(&vec![1, 0, 2, 2], &vec![2, 2, 0]));
    assert!(is_sub_array(&vec![1, 0, 2, 2], &vec![2, 2]));
    assert!(is_sub_array(&vec![1, 0, 2, 2], &vec![1, 0]));

    assert_eq!(
        sub_array_at_index(&vec![1, 0, 2, 2], &vec![1, 0, 2, 2], 0),
        true
    );
    assert_eq!(
        sub_array_at_index(&vec![1, 0, 2, 2], &vec![1, 0, 2, 2], 1),
        false
    );
}

verus! {

fn sub_array_at_index(main: &Vec<i32>, sub: &Vec<i32>, idx: usize) -> (result: bool)
    requires
        sub.len() <= main.len(),
        0 <= idx <= (main.len() - sub.len()),
    ensures
        result == (main@.subrange(idx as int, (idx + sub@.len())) =~= sub@),
{
    let mut i = 0;
    while i < sub.len() {
        if main[idx + i] != sub[i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn is_sub_array(main: &Vec<i32>, sub: &Vec<i32>) -> (result: bool)
    requires
        sub.len() <= main.len(),
    ensures
        result == (exists|k: int, l: int|
            0 <= k <= (main.len() - sub.len()) && l == k + sub.len() && (#[trigger] (main@.subrange(
                k,
                l,
            ))) =~= sub@),
{
    if sub.len() > main.len() {
        return false;
    }
    let mut index = 0;
    while index <= (main.len() - sub.len()) {
        if sub_array_at_index(main, sub, index) {
            return true;
        }
        index = index + 1;
    }
    false
}

} // verus!
