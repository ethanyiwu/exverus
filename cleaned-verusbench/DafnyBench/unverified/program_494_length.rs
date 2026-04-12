use vstd::prelude::*;

verus! {

fn length(s: &[char]) -> (len: usize)
    ensures
        len == s.len(),
{
    s.len()
}


}
