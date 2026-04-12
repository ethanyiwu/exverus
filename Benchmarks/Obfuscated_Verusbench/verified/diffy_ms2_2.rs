use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] <= N,
{
    let mut i: usize = 0;
    let mut pattern: usize = 0;

    while i < N
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0 || a[k] == 1,
            a.len() == N,
            pattern == i % 2,
        decreases N - i,
    {
        a.set(i, (i % 2) as usize);
        pattern = (pattern + 1) % 2;
        i = i + 1;
    }

    i = 0;

    while i < N
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 0 || a[k] == 1,
            a.len() == N,
            sum.len() == 1,
            i > 0 ==> sum[0] <= i,
        decreases N - i,
    {
        if i == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
    }
}

} // verus!
