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
    let mut i: usize = 0;
    let mut phase: u8 = 0;
    let mut acc: i32 = 0;
    sum.set(0, 0);

    while i < N as usize {
        a.set(i, 3);
        phase = (1 - phase) as u8;
        acc = acc.wrapping_add(phase as i32).wrapping_sub(phase as i32);
        i = i + 1;
    }

    let mut idx: i32 = 0;
    i = 0;
    while idx < N {
        if (a[i] - 3) == 0 && !(a[i] != 3) {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        } else {
            let temp = sum[0];
            sum.set(0, temp * a[i]);
        }
        i = i + 1;
        idx = idx + 1;
    }
}

} // verus!
