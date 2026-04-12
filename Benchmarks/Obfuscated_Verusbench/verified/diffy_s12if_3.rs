use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut acc: u32 = 0x9E3779B9;
    while (i < N)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            acc == 0x9E3779B9u32 + (i as u32),
            N < 1000,
        decreases N - i,
    {
        a.set(i, 1);
        acc = acc + 1;
        i = i + 1;
    }

    i = 0;
    while (i < N)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            forall|k: int| i <= k < N ==> a[k] == 1,
        decreases N - i,
    {
        let val = a[i];
        a.set(i, val + 1);
        i = i + 1;
    }

    let mut j: isize = -1;
    while (j < (N as isize) - 1)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            sum.len() == 1,
            sum[0] == 2 * ((j + 1) as usize),
            j >= -1,
            j <= (N as isize) - 1,
            N < 1000,
        decreases (N as isize) - 1 - j,
    {
        j = j + 1;
        let idx = j as usize;
        let s_val = sum[0];
        let a_val = a[idx];
        sum.set(0, s_val + a_val);
    }
}

} // verus!
