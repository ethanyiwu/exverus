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
    while i1 < i2
        invariant
            0 <= i1 <= i2 < v.len(),
            exists|i: int| i1 <= i <= i2 && k == v[i],
            forall|i: int, j: int| 0 <= i <= j < v.len() ==> v[i] <= v[j],
            s == 0 || s == 1,
        decreases i2 - i1,
    {
        a = a ^ i1 ^ i2;

        let ix = if s == 0 {
            i1 + (i2 - i1) / 2
        } else {
            i1 + (i2 - i1) / 2
        };

        assert(ix == i1 + (i2 - i1) / 2) by {
            if s == 0 {
            } else {
            }
        }

        assert(ix >= i1 && ix <= i2) by {
            assert(i1 <= i1 + (i2 - i1) / 2 <= i2);
        }

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
