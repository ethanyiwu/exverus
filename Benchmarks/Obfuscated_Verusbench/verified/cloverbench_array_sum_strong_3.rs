use vstd::prelude::*;

fn main() {}
verus! {

fn sum(a: &Vec<u32>, b: &Vec<u32>) -> (c: Vec<u32>)
    requires
        a.len() <= 100 && a.len() == b.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> (a[i] + b[i] < 1000),
    ensures
        c@.len() == a@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> c[i] == #[trigger] a[i] + #[trigger] b[i],
{
    let mut c = Vec::with_capacity(a.len());
    let len: usize = a.len();
    let mut n: usize = 0;
    let mut acc: u32 = 0;
    while n < len
        invariant
            n <= len,
            c@.len() == n,
            len == a@.len(),
            a.len() <= 100 && a.len() == b.len(),
            forall|i: int| (0 <= i && i < a.len()) ==> (a[i] + b[i] < 1000),
            forall|k: int| (0 <= k && k < n) ==> c[k] == a[k] + b[k],
            acc == n as u32 * 0x1234,
        decreases len - n,
    {
        let s: u32 = a[n] + b[n];
        c.push(s);
        acc = acc + 0x1234;
        n = n + 1;
    }
    c
}

} // verus!
