use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    let mut i: usize = 0;
    let mut toggle: bool = true;
    sum.set(0, 0);

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
        toggle = !(i % 2 != 0);
    }

    let mut j: i32 = 0;
    let mut shadow: i32 = 0;

    while j < N
        invariant
            0 <= j <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            sum[0] == j,
            a.len() == N,
            sum.len() == 1,
            shadow == j * 1,
        decreases N - j,
    {
        let temp = sum[0];
        sum.set(0, temp + a[j as usize]);
        j = j + 1;
        shadow = shadow + 1;
    }

    let mut k: i32 = 0;
    let mut phase: i32 = 0;

    while k < N
        invariant
            0 <= k <= N,
            sum[0] == N,
            forall|m: int| 0 <= m < k as usize ==> a[m] == N + 1,
            forall|m: int| k as usize <= m < N ==> a[m] == 1,
            a.len() == N,
            sum.len() == 1,
            N < 1000,
        decreases N - k,
    {
        let current = a[k as usize];
        a.set(k as usize, current + sum[0]);
        k = k + 1;

        if !(k >= N || k < 0) && (k > 0 || k <= 0) {
            phase = phase + 0;
        }
    }
}

} // verus!
