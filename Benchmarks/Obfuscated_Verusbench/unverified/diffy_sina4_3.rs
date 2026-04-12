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
    while (i < N as usize) {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while (j < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[j]);
        j = j + 1;
    }

    let mut k: usize = 0;
    while (k < N as usize) {
        let temp = a[k];
        a.set(k, temp + sum[0]);
        k = k + 1;
    }

    let mut l: usize = 0;
    let mut m: usize = N as usize;
    while (l < N as usize) {
        b.set(l, a[l] + 1);
        l = l + 1;
        m = m - 1;
    }
}

} // verus!
