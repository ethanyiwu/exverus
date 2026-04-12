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

    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i as int ==> a[j] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1);
        shadow = shadow.wrapping_add(i as i32).wrapping_mul(7919);
        i = i + 1;
    }

    dir = 0;
    i = 0;
    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i as int ==> a[j] == 3,
            forall|j: int| i as int <= j < N ==> a[j] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
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
    while (i < N as usize)
        invariant
            i <= N as usize,
            forall|j: int| 0 <= j < N ==> a[j] == 3,
            sum.len() == 1,
            sum[0] == 3 * i as int,
            N <= 1000,
            a.len() == N,
        decreases N as usize - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        shadow = 0i32.wrapping_sub(shadow.wrapping_add(a[i] as i32));
        i = i + 1;
    }
}

} // verus!
