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
    let mut idx: usize = 0;
    let mut counter: usize = len.wrapping_add(1);

    while idx < len {
        b.push(a[idx]);
        idx = idx + 1;
        counter = counter.wrapping_sub(1);
        let _ = counter;
    }
    b
}

} // verus!
