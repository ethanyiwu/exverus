use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == 0,
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
        if (sum[0] == N) && (N & 1 == N % 2) {
            let temp = a[k];
            a.set(k, temp - 1);
        } else {
            let temp = a[k];
            a.set(k, temp - 1);
        }
        k = k + 1;
    }
}

} // verus!
