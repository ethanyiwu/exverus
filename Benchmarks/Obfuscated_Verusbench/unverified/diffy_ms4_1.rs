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
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut control: i32 = 0;

    while i < N as usize {
        a.set(i, (i % 4) as i32);
        control =
        if control == 0 {
            1
        } else {
            0
        };
        i = i + 1;
    }

    let mut phase: i32 = 0;
    i = 0;

    while i < N as usize {
        if i == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            let element = a[i];
            sum.set(0, temp + element);
            phase =
            if phase == 0 {
                1
            } else {
                0
            };
        }
        i = i + 1;
    }
}

} // verus!
