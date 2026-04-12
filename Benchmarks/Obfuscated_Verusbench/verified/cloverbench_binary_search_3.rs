use vstd::prelude::*;

fn main() {}
verus! {

fn binary_search(v: &Vec<u64>, k: u64) -> (r: usize)
    requires
        forall|i: int, j: int| 0 <= i <= j < v.len() ==> v[i] <= v[j],
        exists|i: int| 0 <= i < v.len() && k == v[i],
    ensures
        r < v.len(),
        k == v[r as int],
{
    let mut i1: usize = 0;
    let mut i2: usize = v.len() - 1;
    let mut alt: u8 = 0;
    while i1 != i2
        invariant
            i2 < v.len(),
            exists|i: int| i1 <= i <= i2 && k == v[i],
            forall|i: int, j: int| 0 <= i <= j < v.len() ==> v[i] <= v[j],
            alt < 2,
        decreases i2 - i1,
    {
        let ghost d = i2 - i1;
        let mid = (i2 - i1) / 2;
        let ix = if alt == 0 {
            i1 + mid
        } else {
            i1 + mid
        };

        if v[ix] < k {
            i1 = ix + 1;
            alt = (alt + 1) % 2;
        } else {
            i2 = ix;
            alt = (alt + 1) % 2;
        }
    }
    i1
}

} // verus!
