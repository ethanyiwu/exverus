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
        forall|k: int| 0 <= k < N ==> a[k] == 2 * N + 1,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while (j < N as usize)
        invariant
            forall|k: int| 0 <= k < j ==> b[k] == 1,
            b.len() == N,
        decreases (N as usize) - j,
    {
        b.set(j, 1);
        j = j + 1;
    }

    let mut k: usize = 0;
    while (k < N as usize)
        invariant
            k <= N,
            sum.len() == 1,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == k,
        decreases (N as usize) - k,
    {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
    }

    let mut m: usize = 0;
    while (m < N as usize)
        invariant
            m <= N,
            forall|k: int| 0 <= k < N ==> b[k] == 1,
            b.len() == N,
            sum[0] == N + m,
            sum.len() == 1,
            N < 1000,
        decreases (N as usize) - m,
    {
        let temp = sum[0];
        sum.set(0, temp + b[m]);
        m = m + 1;
    }

    let mut n: usize = 0;
    while (n < N as usize)
        invariant
            forall|k: int| 0 <= k < n ==> a[k] == 2 * N + 1,
            forall|k: int| n <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == 2 * N,
            sum.len() == 1,
        decreases (N as usize) - n,
    {
        let temp = a[n];
        a.set(n, temp + sum[0]);
        n = n + 1;
    }
}

} // verus!
