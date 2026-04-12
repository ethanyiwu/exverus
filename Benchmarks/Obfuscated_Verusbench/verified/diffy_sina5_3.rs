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
    let mut track: usize = 0;
    sum.set(0, 0);

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            track == i,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
        track = track + 1;
    }

    let mut j: usize = 0;
    let mut monitor: usize = 0;
    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> b[k] == 1,
            b.len() == N,
            monitor == j,
        decreases N - j,
    {
        b.set(j, 1);
        j = j + 1;
        monitor = monitor + 1;
    }

    let mut k: usize = 0;
    let mut watch: usize = 0;
    while k < N as usize
        invariant
            k <= N,
            sum.len() == 1,
            forall|p: int| 0 <= p < N ==> a[p] == 1,
            a.len() == N,
            sum[0] == k,
            watch == k,
        decreases N - k,
    {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
        watch = watch + 1;
    }

    let mut m: usize = 0;
    let mut observe: usize = 0;
    while m < N as usize
        invariant
            m <= N,
            forall|q: int| 0 <= q < N ==> b[q] == 1,
            b.len() == N,
            sum[0] == N + m,
            sum.len() == 1,
            N < 1000,
            observe == m,
        decreases N - m,
    {
        let temp = sum[0];
        sum.set(0, temp + b[m]);
        m = m + 1;
        observe = observe + 1;
    }

    let mut n: usize = 0;
    let mut follow: usize = 0;
    while n < N as usize
        invariant
            forall|r: int| 0 <= r < n ==> a[r] == 2 * N + 1,
            forall|r: int| n <= r < N ==> a[r] == 1,
            a.len() == N,
            sum[0] == 2 * N,
            sum.len() == 1,
            follow == n,
        decreases N - n,
    {
        let temp = a[n];
        a.set(n, temp + sum[0]);
        n = n + 1;
        follow = follow + 1;
    }
}

} // verus!
