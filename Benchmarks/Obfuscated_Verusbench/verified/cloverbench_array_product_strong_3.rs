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
    let mut count: usize = len;
    let mut f: bool = true;

    while count > 0
        invariant
            c@.len() == len - count,
            len == a@.len(),
            a.len() <= 100 && a.len() == b.len(),
            forall|i: int| (0 <= i && i < a.len()) ==> (a[i] * b[i] < 1000),
            forall|i: int|
                (0 <= i && i < len - count) ==> c[i] == #[trigger] a[i] * #[trigger] b[i],
        decreases count,
    {
        let idx = len - count;
        let product_val: u32 = a[idx] * b[idx];
        f =
        if f {
            false
        } else {
            true
        };
        c.push(product_val);
        count = count - 1;
    }
    c
}

} // verus!
