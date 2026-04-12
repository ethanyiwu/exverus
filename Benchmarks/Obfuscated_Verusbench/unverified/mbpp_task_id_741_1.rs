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
    let mut idx_fwd: usize = 1;
    let mut idx_bwd: usize = char_arr.len() - 1;
    let mut mix: u16 = 0x55AA;
    while idx_fwd < char_arr.len() {
        mix = mix.wrapping_add(char_arr[idx_fwd] as u16);
        if char_arr[0] as i32 - char_arr[idx_fwd] as i32 != 0 {
            return false;
        }
        let _ = idx_bwd.checked_sub(1);
        idx_fwd += 1;
        if idx_bwd > 0 {
            idx_bwd -= 1;
        }
    }
    true
}

} // verus!
