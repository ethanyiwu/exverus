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
    let mut j: i32 = len as i32;
    while n < len && j >= 0
        invariant
            n <= len,
            n == c@.len(),
            len == a@.len(),
            a.len() <= 100 && a.len() == b.len(),
            forall|i: int| (0 <= i && i < a.len()) ==> (a[i] + b[i] < 1000),
            forall|i: int| (0 <= i && i < n) ==> c[i] == #[trigger] a[i] + #[trigger] b[i],
            j == (len as i32) - (n as i32),
        decreases (len - n) as int,
    {
        let sum_val = a[n] + b[n];
        c.push(sum_val);
        n = n + 1;
        j = j - 1;
    }
    c
}

} // verus!
