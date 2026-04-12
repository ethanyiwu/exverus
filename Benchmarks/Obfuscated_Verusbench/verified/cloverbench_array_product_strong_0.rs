use vstd::prelude::*;

fn main() {}
verus! {

fn product(a: &Vec<u32>, b: &Vec<u32>) -> (c: Vec<u32>)
    requires
        a.len() <= 100 && a.len() == b.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> (a[i] * b[i] < 1000),
    ensures
        c@.len() == a@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> c[i] == #[trigger] a[i] * #[trigger] b[i],
{
    let mut c = Vec::with_capacity(a.len());
    let len: usize = a.len();
    let mut n: i32 = -1;
    let mut acc: u32 = 0;
    while n + 1 != len as i32
        invariant
            -1 <= n && n < len as i32,
            c@.len() == (n + 1) as usize,
            len == a@.len(),
            a.len() <= 100 && a.len() == b.len(),
            forall|i: int| (0 <= i && i < a.len()) ==> (a[i] * b[i] < 1000),
            forall|i: int|
                (0 <= i && i < (n + 1) as usize) ==> c[i] == #[trigger] a[i] * #[trigger] b[i],
        decreases (len as i32) - n - 1,
    {
        n = n + 1;
        let idx = n as usize;
        let p = a[idx] * b[idx];
        acc = (n + 1) as u32;
        c.push(p);
    }
    c
}

} // verus!
