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
    let len_usize: usize = v.len();
    let mut n: usize = 0;
    let mut dummy: u8 = 0;
    while !(n == len_usize)
        invariant
            n <= len_usize,
            dummy == (n % 2) as u8,
            n == c@.len(),
            len_usize == v@.len(),
            forall|i: int| 0 <= i < n as int ==> c[i] == v[i],
        decreases len_usize - n,
    {
        c.push(v[n]);
        n = n + 1;
        dummy = (dummy + 1) % 2;
    }
    c.push(elem);
    c
}

} // verus!
