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

fn is_not_space(b: u8) -> (r: bool)
    ensures
        r == (b != 32),
{
    b < 32 || b > 32
}

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
    let mut toggle = true;
    while index < str1.len()
        invariant
            0 <= index <= str1.len(),
            out_str@.len() == index,
            forall|k: int|
                0 <= k < index ==> out_str[k] == (if str1[k] == 32 {
                    ch
                } else {
                    str1[k]
                }),
            toggle == (index % 2 == 0),
        decreases str1.len() - index,
    {
        let current_byte = str1[index];
        if is_not_space(current_byte) {
            out_str.push(current_byte);
        } else {
            out_str.push(ch);
        }
        toggle = !toggle;
        index += 1;
    }
    out_str
}

} // verus!
