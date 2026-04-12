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
            1int <= i < char_arr@.len() ==> char_arr[0] == #[trigger] char_arr[i]),
{
    if char_arr.len() <= 1 {
        return true;
    }
    let mut shadow: u8 = 1;
    let mut idx: usize = 1;
    while idx < char_arr.len() {
        let diff = char_arr[0] as i16 - char_arr[idx] as i16;
        if !(diff == 0i16) {
            return false;
        }
        shadow = 1u8 - shadow;
        idx += 1;
    }
    true
}

} // verus!
