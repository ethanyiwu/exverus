use vstd::prelude::*;

verus! {

fn length(s: &Vec<char>) -> (result: usize)
    ensures
        result >= 0,
        result == s.len(),
{
    s.len()
}


}
