use vstd::prelude::*;

fn main() {}
verus! {

fn append(v: &Vec<u64>, elem: u64) -> (c: Vec<u64>)
    requires
        v.len() <= 100,
    ensures
        c@.len() == v@.len() + 1,
        forall|i: int| (0 <= i && i < v.len()) ==> c[i] == v[i],
        c@.last() == elem,
{
    let mut c = Vec::with_capacity(v.len() + 1);
    let mut forward: usize = 0;
    let mut backward: usize = v.len();
    let len: usize = v.len();

    while forward < len
        invariant
            backward == len - forward,
            forward == c@.len(),
            len == v@.len(),
            forall|i: int| 0 <= i < forward ==> c[i] == v[i],
        decreases len - forward,
    {
        c.push(v[forward]);
        forward = forward + 1;
        backward = backward - 1;
    }
    c.push(elem);
    c
}

} // verus!
