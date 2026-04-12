use vstd::prelude::*;

fn main() {}
verus! {

fn copy(a: &Vec<u64>) -> (b: Vec<u64>)
    requires
        a.len() <= 100,
    ensures
        b@.len() == a@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> b[i] == a[i],
{
    let mut b = Vec::with_capacity(a.len());
    let len: usize = a.len();
    let mut pos: usize = 0;
    let mut rem: usize = len;
    let mut flag: u64 = 1;
    while (pos < len) == (flag != 0)
        invariant
            rem == len - pos,
            pos == b@.len(),
            len == a@.len(),
            forall|i: int| (0 <= i && i < pos) ==> b[i] == a[i],
            flag == 1,
        decreases len - pos,
    {
        b.push(a[pos]);
        pos = pos + 1;
        rem = rem - 1;
    }
    b
}

} // verus!
