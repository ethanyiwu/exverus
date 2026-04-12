use vstd::prelude::*;

verus! {

fn length(s: &Vec<char>) -> (result: usize)
    ensures
        result == s.len(),
{
    s.len()
}


}
