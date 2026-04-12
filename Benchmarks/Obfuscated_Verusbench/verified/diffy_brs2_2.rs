use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
    ensures
        sum[0] <= 2 * N,
{
    let mut mix: i32 = 0x5A5A;
    let mut j: isize = -1;
    while (j < (N - 1) as isize)
        invariant
            forall|k: int| 0 <= k < (j + 1) as usize ==> a[k] == 2 || a[k] == 0,
            a.len() == N,
            j >= -1,
        decreases (N as isize) - j - 1,
    {
        j = j + 1;
        let i = j as usize;
        if ((i & 1) == 0) {
            a.set(i, 2);
        } else {
            a.set(i, 0);
        }
        mix = mix ^ (i as i32).wrapping_mul(0x1234);
        if mix > i32::MAX {
        }
    }

    let mut k: isize = -1;
    let mut acc: i32 = 0xDEAD;
    while (k < N as isize - 1)
        invariant
            k >= -1,
            k < N as isize,
            forall|p: int| 0 <= p < N ==> a[p] == 2 || a[p] == 0,
            a.len() == N,
            sum.len() == 1,
            k >= 0 ==> sum[0] <= 2 * (k as usize),
            N < 1000,
        decreases (N as isize) - k - 1,
    {
        k = k + 1;
        let i = k as usize;
        if i == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        acc = acc.wrapping_add(i as i32).wrapping_sub(1);
        if acc < 0 {
        }
    }
}

} // verus!
