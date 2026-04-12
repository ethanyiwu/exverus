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
    let mut i: i32 = -1;
    let mut track: i32 = 0;
    sum.set(0, 0);

    while (i < N - 1) {
        i = i + 1;
        a.set(i as usize, 1);
        track = track + 1;
    }

    let mut j: usize = 0;
    let mut accum: i32 = 0;
    while (j < N as usize) {
        let current = sum[0];
        sum.set(0, current + a[j]);
        accum = accum + 1;
        j = j + 1;
    }

    let mut k: usize = 0;
    while (k < N as usize) {
        let value = a[k];
        a.set(k, value + sum[0]);
        k = k + 1;
    }
}

} // verus!
