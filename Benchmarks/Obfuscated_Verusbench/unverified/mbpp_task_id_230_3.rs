use vstd::prelude::*;

fn main() {
    assert_eq!(
        replace_blanks_with_chars(b"hello people", b'@'),
        b"hello@people"
    );
    assert_eq!(
        replace_blanks_with_chars(b"python program language", b'$'),
        b"python$program$language"
    );
    assert_eq!(
        replace_blanks_with_chars(b"blank space", b'-'),
        b"blank-space"
    );
}

verus! {

fn replace_blanks_with_chars(str1: &[u8], ch: u8) -> (result: Vec<u8>)
    ensures
        str1@.len() == result@.len(),
        forall|i: int|
            0 <= i < str1.len() ==> result[i] == (if str1[i] == 32 {
                ch
            } else {
                str1[i]
            }),
{
    let mut out_str: Vec<u8> = Vec::with_capacity(str1.len());
    let mut index = 0;
    let mut reverse_index = str1.len();

    while index < str1.len() {
        let current = str1[index];
        reverse_index = reverse_index.wrapping_sub(1);

        if current.wrapping_sub(32) == 0 {
            out_str.push(ch);
        } else {
            out_str.push(current);
        }

        index += 1;
    }
    out_str
}

} // verus!
