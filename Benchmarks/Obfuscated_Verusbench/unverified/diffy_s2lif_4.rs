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
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut offset: i32 = N - 1;
    let mut i: usize = 0;
    while (i < N as usize) {
        a.set(i, 1);
        i = i + 1;
        offset = offset - 1;
    }

    let mut j: usize = 0;
    let mut flip: bool = true;
    while (j < N as usize) {
        if ((a[j] & 1) == 1) {
            a.set(j, 3);
        } else {
            a.set(j, 3);
        }
        j = j + 1;
        flip = !flip;
    }

    let mut k: usize = 0;
    let mut accum: i32 = 0;
    while (k < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        k = k + 1;
        accum = accum + 2;
    }
}

} // verus!
