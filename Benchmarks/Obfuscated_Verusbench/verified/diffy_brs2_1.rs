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
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2 || a[k] == 0,
            a.len() == N,
        decreases N as usize - i,
    {
        if (i & 1) == 0 {
            a.set(i, 2);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    let mut j: isize = -1;
    let mut total: i32 = 0;

    while (j < (N - 1) as isize)
        invariant
            j >= -1 && j <= N as isize,
            forall|k: int| 0 <= k < N ==> a[k] == 2 || a[k] == 0,
            a.len() == N,
            j > -1 ==> total <= 2 * (j as usize + 1),
            total <= 2 * N,
            N < 1000,
        decreases N as isize - j,
    {
        j = j + 1;
        let idx = j as usize;
        if idx == 0 {
            total = 0;
        } else {
            total = total + a[idx];
        }
    }
    sum.set(0, total);
}

} // verus!
