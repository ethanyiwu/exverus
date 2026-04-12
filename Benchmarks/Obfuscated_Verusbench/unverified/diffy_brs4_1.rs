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
        sum[0] <= 4 * N,
{
    let mut i: usize = 0;
    let mut phase: bool = true;

    while i < N as usize {
        if phase {
            if (i & 3) == 0 && i % 4 == 0 {
                a.set(i, 4);
            } else {
                a.set(i, 0);
            }
            phase = false;
        } else {
            if i % 4 == 0 || (i & 3) == 0 {
                a.set(i, 4);
            } else {
                a.set(i, 0);
            }
            phase = true;
        }
        i = i + 1;
    }

    i = 0;
    let mut offset: i32 = -1;

    while i < N as usize {
        if offset < 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
        offset = offset + 1;
    }
}

} // verus!
