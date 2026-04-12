use vstd::prelude::*;

verus! {

pub fn deep_copy_seq(s: &Vec<i32>) -> (copy: Vec<i32>)
    requires
        s.len() < 1000000,
    ensures
        copy.len() == s.len(),
        forall|i: nat| 0 <= i < s.len() ==> copy[i as int] == s[i as int],
{
    let mut new_seq: Vec<i32> = Vec::new();
    for i in iter: 0..s.len()
        invariant
            new_seq.len() == i,
            forall|k: nat| 0 <= k < i ==> new_seq[k as int] == s[k as int],
    {
        new_seq.push(s[i]);
    }
    new_seq
}

fn main() {
}

} // verus!
