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
    sum.set(0, 0);
    let mut i: usize = 0;
    while i < N as usize
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 1,
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while j < N as usize
        invariant
            b.len() == N,
            forall|k: int| 0 <= k < j ==> b[k] == 1,
        decreases N as usize - j,
    {
        b.set(j, 1);
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut phase: i32 = 0;
    while k < N as usize
        invariant
            k <= N as usize,
            sum.len() == 1,
            a.len() == N,
            sum[0] == k,
            forall|p: int| 0 <= p < N ==> a[p] == 1,
            phase == k as i32,
        decreases N as usize - k,
    {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
        phase = phase + 1;
    }

    k = 0;
    phase = 0;
    while k < N as usize
        invariant
            k <= N as usize,
            sum.len() == 1,
            b.len() == N,
            sum[0] == N + k,
            forall|p: int| 0 <= p < N ==> b[p] == 1,
            N < 1000,
            phase == k as i32,
        decreases N as usize - k,
    {
        let temp = sum[0];
        sum.set(0, temp + b[k]);
        k = k + 1;
        phase = phase + 1;
    }
}

} // verus!
