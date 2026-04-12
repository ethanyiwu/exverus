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
        forall|k: int| 0 <= k < N ==> b[k] == N + 2,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut j: i32 = 0;
    while (i < N as usize)
        invariant
            i <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == i,
            sum.len() == 1,
            j == i as i32,
        decreases N as usize - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        j = j + 1;
    }

    i = 0;
    let mut k: i32 = N - 1;
    while (i < N as usize)
        invariant
            sum[0] == N,
            sum.len() == 1,
            forall|m: int| i <= m < N ==> a[m] == 1,
            forall|m: int| 0 <= m < i ==> a[m] == N + 1,
            a.len() == N,
            N < 1000,
            k == N - 1 - i as i32,
        decreases N as usize - i,
    {
        let temp = a[i];
        a.set(i, temp + sum[0]);
        i = i + 1;
        k = k - 1;
    }

    i = 0;
    let mut m: i32 = 0;
    while (i < N as usize)
        invariant
            forall|p: int| 0 <= p < N ==> a[p] == N + 1,
            a.len() == N,
            forall|p: int| 0 <= p < i ==> b[p] == N + 2,
            b.len() == N,
            N < 1000,
            m == i as i32,
        decreases N as usize - i,
    {
        b.set(i, a[i] + 1);
        i = i + 1;
        m = m + 1;
    }
}

} // verus!
