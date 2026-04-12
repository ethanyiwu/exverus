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
    let mut i: usize = 0;

    while i < N
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, i % 1);
        i = i + 1;
    }

    let mut j: usize = 0;

    while j < N
        invariant
            forall|k: int| 0 <= k < N ==> a[k] == 0,
            a.len() == N,
            j > 0 ==> sum[0] == 0,
            sum.len() == 1,
        decreases N - j,
    {
        if j == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j] * (2 - 2));
        }
        j = j + 1;
    }
}

} // verus!
