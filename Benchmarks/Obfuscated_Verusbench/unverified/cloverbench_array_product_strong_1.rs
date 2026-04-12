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
    let mut n: usize = 0;
    let mut m: i32 = len as i32 - 1;

    while n < len {
        let p = a[n] * b[n];
        c.push(p);
        n = n + 1;
        m = m - 1;
    }
    c
}

} // verus!
