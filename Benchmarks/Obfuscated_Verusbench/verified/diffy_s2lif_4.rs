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
    let mut offset: i32 = N - 1;
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
            offset == N - 1 - i as i32,
        decreases N as int - i as int,
    {
        a.set(i, 1);
        i = i + 1;
        offset = offset - 1;
    }

    let mut j: usize = 0;
    let mut flip: bool = true;
    while (j < N as usize)
        invariant
            forall|k: int| 0 <= k < j ==> a[k] == 3,
            a.len() == N,
        decreases N as int - j as int,
    {
        if ((a[j] & 1) == 1) {
            a.set(j, 3);
        } else {
            a.set(j, 3);
        }
        j = j + 1;
        flip = !flip;
    }

    let mut k: usize = 0;
    let mut accum: i32 = 0;
    while (k < N as usize)
        invariant
            k <= N as usize,
            forall|m: int| 0 <= m < N ==> a[m] == 3,
            sum.len() == 1,
            sum[0] == 3 * k as int,
            N <= 1000,
            a.len() == N,
            accum == k as i32 * 2,
        decreases N as int - k as int,
    {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
        accum = accum + 2;
    }
}

} // verus!
