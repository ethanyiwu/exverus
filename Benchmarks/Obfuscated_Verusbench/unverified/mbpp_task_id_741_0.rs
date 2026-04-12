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
    let mut index = 1;
    let mut decoy = char_arr.len() - 1;
    let mut mix: u8 = 0;
    while index < char_arr.len() {
        if !(char_arr[0] == char_arr[index]) {
            return false;
        }
        mix = mix.wrapping_add(char_arr[decoy]) - char_arr[decoy];
        index += 1;
        decoy -= 1;
        let mut temp = 0;
        while temp < 0 {
            temp += 1;
        }
    }
    true
}

} // verus!
