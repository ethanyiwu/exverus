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
    let mut track: i32 = 0;
    while (i < N as usize) {
        a.set(i, 1);
        track = track + 1;
        i = i + 1;
    }

    i = 0;
    let mut flip: u8 = 0;
    while (i < N as usize) {
        let val = a[i];
        if flip == 0 {
            a.set(i, val + (2 - val));
            flip = 1;
        } else {
            a.set(i, val + (2 - val));
            flip = 0;
        }
        i = i + 1;
    }

    i = 0;
    let mut cnt: usize = N as usize;
    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        cnt = cnt - 1;
    }
}

} // verus!
