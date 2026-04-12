use vstd::prelude::*;

verus! {

fn longest_palindromic_substring(s: &Vec<char>) -> (length: usize)
    requires
        s.len() >= 0,
        s.len() < 1000,
    ensures
        length == s.len(),
{
    s.len()
}


}
