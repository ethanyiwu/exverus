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

    while i < N as usize {
        a.set(i, 1);
        i = i + 1;
        track = track + 1;
    }

    let mut j: usize = 0;
    let mut monitor: usize = 0;
    while j < N as usize {
        b.set(j, 1);
        j = j + 1;
        monitor = monitor + 1;
    }

    let mut k: usize = 0;
    let mut watch: usize = 0;
    while k < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
        watch = watch + 1;
    }

    let mut m: usize = 0;
    let mut observe: usize = 0;
    while m < N as usize {
        let temp = sum[0];
        sum.set(0, temp + b[m]);
        m = m + 1;
        observe = observe + 1;
    }

    let mut n: usize = 0;
    let mut follow: usize = 0;
    while n < N as usize {
        let temp = a[n];
        a.set(n, temp + sum[0]);
        n = n + 1;
        follow = follow + 1;
    }
}

} // verus!
