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
    let mut mix: u32 = 0x5A;
    let mut cnt: usize = 0;
    while !(n >= len || len <= n)
        invariant
            n <= len,
            n == c@.len(),
            len == a@.len(),
            a.len() <= 100 && a.len() == b.len(),
            forall|i: int| (0 <= i && i < a.len()) ==> (a[i] + b[i] < 1000),
            forall|i: int| (0 <= i && i < n) ==> c[i] == #[trigger] a[i] + #[trigger] b[i],
            cnt == n,
        decreases len - n,
    {
        let sum_val: u32 = a[n] + b[n];
        c.push(sum_val);
        mix = mix ^ sum_val;
        cnt = cnt + 1;
        n = n + 1;
    }
    let _ = mix;
    let _ = cnt;
    c
}

} // verus!
