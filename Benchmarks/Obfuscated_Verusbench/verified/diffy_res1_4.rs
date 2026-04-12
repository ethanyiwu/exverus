use vstd::prelude::*;
fn main() {}

verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] <= 2 * N,
{
    let mut idx: i32 = -1;
    sum.set(0, 0);

    while idx + 1 < N
        invariant
            a.len() == N,
            -1 <= idx < N,
            forall|k: int| 0 <= k <= idx ==> a[k] == 1,
        decreases N - (idx + 1),
    {
        idx = idx + 1;
        a.set(idx as usize, 1);
    }

    idx = -1;
    while N - (idx + 1) > 0
        invariant
            b.len() == N,
            -1 <= idx < N,
            forall|k: int| 0 <= k <= idx ==> b[k] == 1,
        decreases N - (idx + 1),
    {
        idx = idx + 1;
        b.set(idx as usize, 1);
    }

    let mut pos: i32 = 0;
    while pos < N
        invariant
            0 <= pos <= N,
            sum.len() == 1,
            sum[0] == pos as usize,
            a.len() == N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
        decreases N - pos,
    {
        let temp = sum[0];
        sum.set(0, temp + a[pos as usize]);
        pos = pos + 1;
    }

    pos = 0;
    while (N - pos) != 0
        invariant
            0 <= pos <= N,
            sum.len() == 1,
            b.len() == N,
            sum[0] == N + pos as usize,
            N < 1000,
            forall|k: int| 0 <= k < N ==> b[k] == 1,
        decreases N - pos,
    {
        let temp = sum[0];
        sum.set(0, temp + b[pos as usize]);
        pos = pos + 1;
    }
}

} // verus!
