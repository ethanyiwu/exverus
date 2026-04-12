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
    let mut n: isize = 0;
    let mut mix: u64 = 0;

    while n != len as isize
        invariant
            n <= len as isize,
            n >= 0,
            b@.len() == n as usize,
            len == a@.len(),
            forall|i: int| (0 <= i && i < n as int) ==> b[i] == a[i],
            mix == n as u64 * 2,
        decreases (len as isize - n) as int,
    {
        let idx = n as usize;
        b.push(a[idx]);
        mix = mix + 2;
        n = n + 1;
    }
    b
}

} // verus!
