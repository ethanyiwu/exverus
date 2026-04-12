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
    let mut n: i64 = -1;
    let mut acc: u64 = 0;
    while (n + 1) < (len as i64) {
        n = n + 1;
        let idx: usize = n as usize;
        b.push(a[idx]);
        acc = n as u64;
    }
    b
}

} // verus!
