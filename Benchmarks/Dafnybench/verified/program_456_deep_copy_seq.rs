use vstd::prelude::*;

verus! {

fn deep_copy_seq(s: Vec<i32>) -> (copy: Vec<i32>)
    requires
        s.len() < 1000,
    ensures
        copy.len() == s.len(),
        forall|i: int| 0 <= i < s.len() ==> copy[i] == s[i],
{
    let mut new_seq: Vec<i32> = Vec::new();
    for i in 0..s.len()
        invariant
            new_seq.len() == i,
            forall|k: int| 0 <= k < i ==> new_seq[k] == s[k],
    {
        new_seq.push(s[i]);
    }
    new_seq
}

fn main() {
}

} // verus!
