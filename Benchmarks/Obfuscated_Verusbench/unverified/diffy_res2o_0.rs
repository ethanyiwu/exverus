use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, c: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(c).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut mix: i64 = 0;
    sum.set(0, 0);

    while (i < N as usize) {
        a.set(i, 1);
        mix = mix.wrapping_add((i as i64) << 2);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize) {
        b.set(i, 1);
        mix = mix.wrapping_sub((i as i64) * 3);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize) {
        c.set(i, 1);
        mix = mix ^ ((i as i64) + 7);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut k: usize = 0;
    let mut m: usize = 0;
    let mut acc: i32 = 0;

    while (j < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[j]);
        j = j + 1;
        acc = acc.wrapping_add(1);
    }

    while (k < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + b[k]);
        k = k + 1;
        acc = acc.wrapping_sub(1);
    }

    while (m < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + c[m]);
        m = m + 1;
        acc = acc.wrapping_mul(2);
    }
}

} // verus!
