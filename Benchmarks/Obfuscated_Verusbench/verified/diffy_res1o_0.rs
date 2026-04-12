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
    let mut i: i32 = 0;
    let mut track: i32 = 0;

    while i < N
        invariant
            a.len() == N,
            0 <= i <= N,
            forall|k: int| 0 <= k < i ==> a[k] == 1,
        decreases N - i,
    {
        a.set(i as usize, 1);
        track = i + 1;
        i = i + 1;
    }

    i = 0;
    let mut acc: i32 = 0;
    while i < N
        invariant
            0 <= i <= N,
            sum.len() == 1,
            a.len() == N,
            sum[0] == i,
            acc == i,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i as usize]);
        acc = acc + 1;
        i = i + 1;
    }

    i = 0;
    track = 0;
    while i < N
        invariant
            b.len() == N,
            0 <= i <= N,
            forall|k: int| 0 <= k < i ==> b[k] == 1,
        decreases N - i,
    {
        b.set(i as usize, 1);
        track = i + 1;
        i = i + 1;
    }

    i = 0;
    acc = 0;
    while i < N
        invariant
            0 <= i <= N,
            sum.len() == 1,
            b.len() == N,
            sum[0] == N + i,
            acc == i,
            forall|k: int| 0 <= k < N ==> b[k] == 1,
            N < 1000,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + b[i as usize]);
        acc = acc + 1;
        i = i + 1;
    }
}

} // verus!
