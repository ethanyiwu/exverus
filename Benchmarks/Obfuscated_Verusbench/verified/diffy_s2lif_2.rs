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
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut aux: i32 = 0;
    let mut i: i32 = -1;
    while i + 1 < N
        invariant
            -1 <= i <= N - 1,
            forall|k: int| 0 <= k < i + 1 ==> a[k] == 1,
            a.len() == N,
            aux == i + 1,
        decreases N - i - 1,
    {
        i = i + 1;
        a.set(i as usize, 1);
        aux = aux + 1;
    }

    let mut i: usize = 0;
    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 3,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases (N as usize) - i,
    {
        if !(a[i] != 1) {
            let temp = a[i];
            a.set(i, temp + 2);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        i = i + 1;
    }

    let mut i: i32 = 0;
    let mut track: i32 = 0;
    while i < N
        invariant
            0 <= i <= N,
            forall|j: int| 0 <= j < N ==> a[j] == 3,
            sum.len() == 1,
            sum[0] == 3 * i,
            N <= 1000,
            a.len() == N,
            track == 3 * i,
        decreases N - i,
    {
        let idx = i as usize;
        let temp = sum[0];
        sum.set(0, temp + a[idx]);
        track = track + a[idx];
        i = i + 1;
    }
}

} // verus!
