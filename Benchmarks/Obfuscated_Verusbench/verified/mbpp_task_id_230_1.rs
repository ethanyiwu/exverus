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
    let mut index: usize = 0;
    let mut acc: u8 = 0x55;
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
        decreases str1.len() - index,
    {
        let byte_val = str1[index];
        let is_space = byte_val == 32;
        let output_byte = if is_space {
            ch
        } else {
            byte_val
        };
        out_str.push(output_byte);
        acc = acc ^ output_byte;
        index += 1;
    }
    out_str
}

} // verus!
