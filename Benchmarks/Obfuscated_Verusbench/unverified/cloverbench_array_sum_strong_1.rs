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
    let mut idx_signed: i32 = -1;
    while idx_signed + 1 < len as i32 {
        idx_signed = idx_signed + 1;
        let current_idx = idx_signed as usize;
        let sum_val: u32 = a[current_idx] + b[current_idx];
        c.push(sum_val);
    }
    c
}

} // verus!
