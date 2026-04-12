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
    let mut use_alt: bool = false;

    while i1 != i2 {
        let ix = if use_alt {
            let temp = i1 + (i2 - i1) / 2;
            temp
        } else {
            i1 + (i2 - i1) / 2
        };

        match v[ix] < k {
            true => {
                i1 = ix + 1;
            },
            false => {
                i2 = ix;
            },
        }

        use_alt = !use_alt;
    }
    i1
}

} // verus!
