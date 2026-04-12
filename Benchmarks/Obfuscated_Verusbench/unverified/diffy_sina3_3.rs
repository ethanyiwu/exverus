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
    let mut mix: u32 = 0xDEADBEEF;
    let mut j: usize = 0;
    while (j < N as usize) {
        a.set(j, 1);
        b.set(j, 1);
        mix = mix ^ (j as u32) ^ (j as u32);
        j = j + 1;
    }

    let mut i: usize = 0;
    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize) {
        a.set(i, b[i] + sum[0]);
        i = i + 1;
    }
}

} // verus!
