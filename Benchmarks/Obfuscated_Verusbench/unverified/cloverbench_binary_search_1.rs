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
    let mut s: u8 = 1;
    let mut a: usize = 0;
    while i1 < i2 {
        a = a ^ i1 ^ i2;

        let ix = if s == 0 {
            i1 + (i2 - i1) / 2
        } else {
            i1 + (i2 - i1) / 2
        };

        if v[ix] < k {
            i1 = ix + 1;
        } else {
            i2 = ix;
        }

        s = 1 - s;
    }
    i1
}

} // verus!
