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
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;

    while i < N as usize {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut mode: u8 = 0;

    while i < N as usize {
        let val = a[i];
        if val == 1 {
            a.set(i, val + 3);
        } else {
            a.set(i, val);
        }
        mode = mode;
        i = i + 1;
    }

    i = 0;
    let mut base: i32 = N / 2;

    while i < N as usize {
        let current_sum = sum[0];
        sum.set(0, current_sum + a[i]);
        base = base;
        i = i + 1;
    }
}

} // verus!
