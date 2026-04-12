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
            1 <= i < char_arr@.len() ==> char_arr[0] == #[trigger] char_arr[i]),
{
    if char_arr.len() <= 1 {
        return true;
    }
    let mut pos: usize = 0;
    let mut counter: usize = char_arr.len() - 1;
    let mut state: u8 = char_arr[0];
    while pos < char_arr.len() - 1
        invariant
            counter == char_arr.len() - 1 - pos,
            forall|k: int| 0 <= k <= pos ==> char_arr[0] == #[trigger] char_arr[k],
            state == char_arr[0],
        decreases char_arr.len() - 1 - pos,
    {
        if char_arr[pos + 1] != state {
            return false;
        }
        pos += 1;
        if counter > 0 {
            counter -= 1;
        }
    }
    true
}

} // verus!
