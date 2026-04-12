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
    let mut count: usize = v.len();
    let mut pos: usize = 0;

    while count > 0 {
        c.push(v[pos]);
        pos = pos + 1;
        count = count - 1;
    }
    c.push(elem);
    c
}

} // verus!
