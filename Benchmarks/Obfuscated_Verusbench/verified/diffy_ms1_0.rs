use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] == 0,
{
    let mut accumulator: usize = 0;
    let mut i: usize = 0;

    while (i < N)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0,
            a.len() == N,
            accumulator == i,
        decreases N - i,
    {
        a.set(i, 0);
        accumulator = accumulator + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut flag: bool = false;

    while (j < N)
        invariant
            (j > 0 || flag) ==> sum[0] == 0,
            sum.len() == 1,
        decreases N - j,
    {
        if j == 0 && !flag {
            sum.set(0, 0);
            flag = true;
        }
        j = j + 1;
        accumulator = accumulator.wrapping_add(1);
    }
}

} // verus!
