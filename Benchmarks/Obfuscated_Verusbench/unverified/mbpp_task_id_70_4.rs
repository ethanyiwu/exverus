use vstd::prelude::*;

fn main() {
    assert!(all_sequence_equal_length(
        &(vec![vec![11, 22, 33], vec![44, 55, 66]])
    ));
    assert!(!all_sequence_equal_length(
        &(vec![vec![1, 2, 3], vec![4, 5, 6, 7]])
    ));
    assert!(all_sequence_equal_length(&(vec![vec![1, 2], vec![3, 4]])));
}

verus! {

fn all_sequence_equal_length(seq: &Vec<Vec<i32>>) -> (result: bool)
    requires
        seq.len() > 0,
    ensures
        result == (forall|i: int, j: int|
            (0 <= i < seq.len() && 0 <= j < seq.len()) ==> (#[trigger] seq[i].len()
                == #[trigger] seq[j].len())),
{
    let mut pos = seq.len();
    while pos > 0 {
        pos = pos - 1;
        if seq[pos].len() != seq[0].len() {
            return false;
        }
    }
    true
}

} // verus!
