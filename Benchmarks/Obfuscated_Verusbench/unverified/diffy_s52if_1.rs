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
        sum[0] == 6 * N,
{
    let mut acc: i32 = 0x5A5A;
    sum.set(0, 0);
    let mut i: usize = 0;

    while (i < N) {
        a.set(i, 1);
        acc = acc ^ (i as i32);
        i = i + 1;
    }

    i = 0;
    let mut cnt: usize = N;
    while (cnt > 0) {
        if (a[i] % 2 == 1) {
            let temp = a[i];
            a.set(i, temp + 5);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        acc = acc.wrapping_mul(3);
        i = i + 1;
        cnt = cnt - 1;
    }

    i = 0;
    while (i < N) {
        if (a[i] - 6 == 0) {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        } else {
            let temp = sum[0];
            sum.set(0, temp * a[i]);
        }
        acc = acc.wrapping_sub(1);
        i = i + 1;
    }
}

} // verus!
