use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == 0,
{
    sum.set(0, 0);
    let mut i: usize = 0;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;

    while (j < N as usize)
        invariant
            j <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == j,
            sum.len() == 1,
        decreases N - j,
    {
        let temp = sum[0];
        sum.set(0, temp + a[j]);
        j = j + 1;
    }

    let mut k: usize = 0;

    while (k < N as usize)
        invariant
            forall|pos: int| 0 <= pos < k ==> a[pos] == 0,
            forall|pos: int| k <= pos < N ==> a[pos] == 1,
            a.len() == N,
            sum.len() == 1,
        decreases N - k,
    {
        if (sum[0] == N) && (N & 1 == N % 2) {
            let temp = a[k];
            a.set(k, temp - 1);
        } else {
            let temp = a[k];
            a.set(k, temp - 1);
        }
        k = k + 1;
    }
}

} // verus!
