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
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    sum.set(0, 0);
    let mut state: i32 = 0;
    let mut i: usize = 0;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            state == i as i32,
        decreases N as usize - i,
    {
        a.set(i, 1);
        state = state + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut counter: i32 = 0;

    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> b[k] == 1,
            b.len() == N,
            counter == j as i32,
        decreases N as usize - j,
    {
        b.set(j, 1);
        counter = counter + 1;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut accum: i32 = 0;

    while k < N as usize
        invariant
            k <= N as usize,
            sum.len() == 1,
            forall|p: int| 0 <= p < N ==> a[p] == 1,
            a.len() == N,
            sum[0] == k,
            accum == k as i32,
        decreases N as usize - k,
    {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        accum = accum + 1;
        k = k + 1;
    }

    let mut m: usize = 0;
    let mut phase: i32 = 0;

    while m < N as usize
        invariant
            forall|p: int| 0 <= p < N ==> b[p] == 1,
            forall|p: int| 0 <= p < m ==> a[p] == N + 1,
            a.len() == N,
            b.len() == N,
            sum.len() == 1,
            sum[0] == N,
            N < 1000,
            phase == m as i32,
        decreases N as usize - m,
    {
        a.set(m, b[m] + sum[0]);
        phase = phase + 1;
        m = m + 1;
    }
}

} // verus!
