use vstd::prelude::*;
use vstd::slice::*;

verus! {

fn string_xor(a: &[char], b: &[char]) -> (result: Vec<char>)
    requires
        a@.len() == b@.len(),
        forall|i: int| 0 <= i < a@.len() as int ==> is_binary_digit(#[trigger] a[i]),
        forall|i: int| 0 <= i < b@.len() as int ==> is_binary_digit(#[trigger] b[i]),
    ensures
        result.len() == a@.len(),
        forall|i: int|
            0 <= i < result.len() as int ==> #[trigger] result[i] == xor_char(a[i], b[i]),
{
    let a_len = a.len();
    let mut result = Vec::with_capacity(a_len);
    #[verifier::loop_isolation(false)]
    for pos in 0..a_len
    {
        if *slice_index_get(a, pos) == *slice_index_get(b, pos) {
            result.push('0');
        } else {
            result.push('1');
        }
    }
    result
}

}
fn main() {}
