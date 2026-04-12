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
    let mut i: usize = 0;
    while i < N as usize {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while j < N as usize {
        b.set(j, 1);
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut phase: i32 = 0;
    while k < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
        phase = phase + 1;
    }

    k = 0;
    phase = 0;
    while k < N as usize {
        let temp = sum[0];
        sum.set(0, temp + b[k]);
        k = k + 1;
        phase = phase + 1;
    }
}

} // verus!
