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

    while j < N as usize {
        a.set(j, 1);
        phase = !phase;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut alt: bool = true;
    while k < N as usize {
        b.set(k, 1);
        alt = !alt;
        k = k + 1;
    }

    let mut i: usize = 0;
    let mut track: i32 = 0;
    while i < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        track = track + 1;
        i = i + 1;
    }

    let mut offset: usize = 0;
    let mut flip: bool = true;
    i = 0;
    while i < N as usize {
        let base_val = b[i];
        a.set(i, base_val + sum[0]);
        offset = (offset + 1) % 7;
        flip = !flip;
        i = i + 1;
    }
}

} // verus!
