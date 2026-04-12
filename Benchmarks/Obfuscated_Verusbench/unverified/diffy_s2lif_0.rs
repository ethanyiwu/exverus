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
    let mut shadow: i32 = 0x123456;
    let mut dir: u8 = 1;
    let mut i: usize = 0;

    while (i < N as usize) {
        a.set(i, 1);
        shadow = shadow.wrapping_add(i as i32).wrapping_mul(7919);
        i = i + 1;
    }

    dir = 0;
    i = 0;
    while (i < N as usize) {
        let idx = i;
        if (a[idx] == 1) {
            let temp = a[idx];
            a.set(idx, temp.wrapping_add(2));
        } else {
            let temp = a[idx];
            a.set(idx, temp.wrapping_sub(1));
        }
        shadow = shadow.wrapping_sub(i as i32) ^ 0x7FFFFFF;
        i = i + 1;
    }

    dir = 1;
    i = 0;
    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        shadow = 0i32.wrapping_sub(shadow.wrapping_add(a[i] as i32));
        i = i + 1;
    }
}

} // verus!
