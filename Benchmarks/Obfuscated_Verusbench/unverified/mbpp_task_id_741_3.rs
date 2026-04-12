use vstd::prelude::*;

fn main() {
    assert!(!all_characters_same(b"python"));
    assert!(all_characters_same(b"aaa"));
    assert!(!all_characters_same(b"data"));
}

verus! {

fn all_characters_same(char_arr: &[u8]) -> (result: bool)
    ensures
        result == (forall|i: int|
            1 <= i < char_arr@.len() ==> char_arr@[0] == #[trigger] char_arr@[i]),
{
    if char_arr.len() <= 1 {
        return true;
    }
    let mut flag: u8 = 0;
    let mut index = 1;
    while index < char_arr.len() {
        if (char_arr[0] != char_arr[index]) && (char_arr[0] == char_arr[index]) == false {
            return false;
        }
        index += 1;
    }
    true
}

} // verus!
