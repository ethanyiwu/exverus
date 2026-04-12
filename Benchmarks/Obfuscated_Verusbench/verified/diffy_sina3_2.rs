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
    let mut phase: bool = false;
    let mut j: usize = 0;

    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - j,
    {
        a.set(j, 1);
        phase = !phase;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut alt: bool = true;
    while k < N as usize
        invariant
            forall|p: int| 0 <= p < k ==> b[p] == 1,
            b.len() == N,
        decreases N as usize - k,
    {
        b.set(k, 1);
        alt = !alt;
        k = k + 1;
    }

    let mut i: usize = 0;
    let mut track: i32 = 0;
    while i < N as usize
        invariant
            i <= N,
            sum.len() == 1,
            forall|q: int| 0 <= q < N ==> a[q] == 1,
            a.len() == N,
            sum[0] == i,
            track == i as i32,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        track = track + 1;
        i = i + 1;
    }

    let mut offset: usize = 0;
    let mut flip: bool = true;
    i = 0;
    while i < N as usize
        invariant
            forall|r: int| 0 <= r < N ==> b[r] == 1,
            forall|s: int| 0 <= s < i ==> a[s] == N + 1,
            a.len() == N,
            b.len() == N,
            sum.len() == 1,
            sum[0] == N,
            N < 1000,
            offset == i % 7,
        decreases N - i,
    {
        let base_val = b[i];
        a.set(i, base_val + sum[0]);
        offset = (offset + 1) % 7;
        flip = !flip;
        i = i + 1;
    }
}

} // verus!
