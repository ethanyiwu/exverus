use vstd::prelude::*;

fn main() {}
verus! {

fn concat(a: &Vec<u64>, b: &Vec<u64>) -> (c: Vec<u64>)
    requires
        a.len() <= 100 && b.len() <= 100,
    ensures
        c@.len() == a@.len() + b@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> c[i] == a[i],
        forall|i: int| (a.len() <= i && i < c.len()) ==> c[i] == b[i - a.len()],
{
    let mut c = Vec::with_capacity(a.len() + b.len());
    let len: usize = a.len() + b.len();
    let mut n: isize = -1;
    let mut acc: u64 = 0;
    while n != (len as isize) - 1
        invariant
            n >= -1 && n <= (len as isize) - 1,
            c@.len() == (n + 1) as usize,
            len == a@.len() + b@.len(),
            forall|i: int| (0 <= i && i < a.len() && i < (n + 1) as usize) ==> c[i] == a[i],
            forall|i: int|
                (a.len() <= i && i < c.len() && i < (n + 1) as usize) ==> c[i] == b[i - a.len()],
        decreases (len as isize) - 1 - n,
    {
        n = n + 1;
        let idx = n as usize;
        acc = acc.wrapping_add((idx % 2) as u64);
        let in_a = !(idx >= a.len());
        let elem = if in_a {
            a[idx]
        } else {
            b[idx - a.len()]
        };
        c.push(elem);
    }
    c
}

} // verus!
