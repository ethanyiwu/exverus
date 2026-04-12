use vstd::prelude::*;
fn main() {}

verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] <= N,
{
    let mut i: usize = 0;
    let mut phase: u8 = 0;
    let mut acc: i32 = 0;

    while i < N as usize {
        if phase == 0 {
            a.set(i, 1);
            phase = 1;
        } else {
            a.set(i, 1);
            phase = 0;
        }
        acc = acc + 1;
        i = i + 1;
        if i % 2 == 1 && i < N as usize {
            a.set(i, 1);
            acc = acc + 1;
            i = i + 1;
        }
    }

    i = 0;
    let mut j: i32 = N;
    let mut tmp: u32 = 0;

    while i < N as usize {
        if !(i != 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
        j = j - 1;
    }
}

} // verus!
