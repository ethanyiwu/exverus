use vstd::prelude::*;

fn main() {
    assert_eq!(count_true(&vec![true, false, true]), 2);
    assert_eq!(count_true(&vec![false, false]), 0);
    assert_eq!(count_true(&vec![true, true, true]), 3);
}

verus! {

spec fn count_boolean(seq: Seq<bool>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_boolean(seq.drop_last()) + if (seq.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

fn count_true(arr: &Vec<bool>) -> (count: u64)
    ensures
        0 <= count <= arr.len(),
        count_boolean(arr@) == count,
{
    let mut index = 0;
    let mut counter = 0;

    while index < arr.len() {
        if (arr[index] as u8) % 2 == 1 {
            counter = counter + 1;
        }
        index = index + 1;
    }
    counter
}

} // verus!
