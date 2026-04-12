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
        sum[0] <= 5 * N,
{
    let mut i: usize = 0;
    let mut shadow: u64 = 3735928559u64;
    let mut toggle: u8 = 1u8;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 5 || a[k] == 0,
            a.len() == N,
        decreases N as usize - i,
    {
        if (i % 5 == 0) {
            a.set(i, 5);
        } else {
            a.set(i, 0);
        }
        shadow = 3735928559u64 + ((i + 1) as u64);
        toggle = 1u8 - ((i + 1) as u8 % 2u8);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut phantom: i64 = 0i64;
    let mut flip: bool = false;

    while (j < N as usize)
        invariant
            j <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 5 || a[k] == 0,
            a.len() == N,
            sum.len() == 1,
            j > 0 ==> sum[0] <= 5 * j,
            N < 1000,
        decreases N as usize - j,
    {
        if (j == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j]);
        }
        flip = !flip;
        j = j + 1;
    }
}

} // verus!
