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
    while (i < N as usize) {
        if (i & 1) == 0 {
            a.set(i, 2);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    let mut j: isize = -1;
    let mut total: i32 = 0;

    while (j < (N - 1) as isize) {
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
