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
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut flip: bool = true;

    while i < N as usize {
        a.set(i, 1);
        i = i + 1;
        flip = !flip;
    }

    i = 0;
    let mut offset: i32 = 0;
    while i < N as usize {
        let current = a[i];
        if current % 2 == 1 {
            a.set(i, current + 1);
        } else {
            a.set(i, current);
        }
        i = i + 1;
        offset = offset + 1;
    }

    i = 0;
    let mut base: i32 = -1;
    while i < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        base = base + 1;
    }
}

} // verus!
