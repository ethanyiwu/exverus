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
    let mut idx: i32 = -(len as i32);
    let mut mix: u64 = 0xDEADBEEF;

    while idx != 0 {
        let pos: usize = (len as i32 + idx) as usize;
        let product_val: u32 = a[pos] * b[pos];
        c.push(product_val);
        let temp = mix;
        mix = temp;
        idx = idx + 1;
    }
    c
}

} // verus!
