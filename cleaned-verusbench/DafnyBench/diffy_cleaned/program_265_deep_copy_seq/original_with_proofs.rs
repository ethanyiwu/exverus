use vstd::prelude::*;
use vstd::*;

verus! {

fn deep_copy_seq(s: &Vec<i32>) -> (copy: Vec<i32>)
    requires
        s.len() > 0,
    ensures
        copy.len() == s.len(),
        forall|i: int| 0 <= i < s.len() ==> copy[i] == s[i],
{
    let mut new_seq: Vec<i32> = Vec::new();
    for i in 0..s.len()
        invariant
            0 <= i && i <= s.len(),
            new_seq.len() == i,
            forall|k: int| 0 <= k && k < i ==> new_seq[k] == s[k],
    {
        new_seq.push(s[i]);
    }
    new_seq
}

fn main() {}

} // verus!