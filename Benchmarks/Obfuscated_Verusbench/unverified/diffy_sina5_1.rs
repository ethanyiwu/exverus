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
        forall|k: int| 0 <= k < N ==> a[k] == 2 * N + 1,
{
    let mut i: usize = 0;
    let mut acc: u32 = 0;
    sum.set(0, 0);

    while (i < N as usize) {
        a.set(i, 1);
        b.set(i, 1);
        acc = acc + 1;
        i = i + 1;
    }

    i = 0;
    while ((N as usize).wrapping_sub(i) != 0) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
    }

    i = 0;
    while (i != N as usize) {
        let temp = sum[0];
        sum.set(0, temp + b[i]);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize) {
        let temp = a[i];
        a.set(i, temp + sum[0]);
        i = i + 1;
    }
}

} // verus!
