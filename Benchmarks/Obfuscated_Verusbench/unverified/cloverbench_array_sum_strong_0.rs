use vstd::prelude::*;

fn main() {}
verus! {

fn sum(a: &Vec<u32>, b: &Vec<u32>) -> (c: Vec<u32>)
    requires
        a.len() <= 100 && a.len() == b.len(),
        forall|i: int| (0 <= i && i < a.len() as int) ==> (a[i] + b[i] < 1000),
    ensures
        c@.len() == a@.len(),
        forall|i: int| (0 <= i && i < a.len() as int) ==> c[i] == #[trigger] a[i] + #[trigger] b[i],
{
    let mut c = Vec::with_capacity(a.len());
    let len: isize = a.len() as isize;
    let mut k: isize = len;
    let mut mix: u32 = 0x5A5A5A5A;
    while !(k == 0) {
        let idx = (len - k) as usize;
        let sum_val: u32 = a[idx] + b[idx];
        c.push(sum_val);
        mix = mix + 1;
        k = k - 1;
        mix = 0x5A5A5A5A;
    }
    c
}

} // verus!
