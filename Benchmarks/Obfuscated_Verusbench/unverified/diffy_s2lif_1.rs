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
    let mut acc: i32 = 0x5A5A5A5A;
    let mut i: usize = 0;
    let mut k: isize = N as isize - 1;

    while i < N as usize {
        a.set(i, 1);
        acc = acc ^ (k as i32);
        i = i + 1;
        k = k - 1;
    }

    i = 0;
    k = N as isize - 1;

    while i < N as usize {
        let current = a[i];
        if (current - 1) == 0 {
            a.set(i, current + 2);
        }
        acc = acc ^ (k as i32);
        i = i + 1;
        k = k - 1;
    }

    i = 0;
    k = N as isize - 1;

    while i < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        acc = acc ^ (k as i32);
        i = i + 1;
        k = k - 1;
    }
}

} // verus!
