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
    let mut toggle: u8 = 0;
    while (i < N as usize) {
        if toggle == 0 {
            a.set(i, 1);
            toggle = 1;
        } else {
            a.set(i, 1);
            toggle = 0;
        }
        i = i + 1;
    }

    i = 0;
    toggle = 0;
    while (i < N as usize) {
        if (a[i] % 2) == 1 {
            if toggle == 0 {
                let temp = a[i];
                a.set(i, temp + 1);
                toggle = 1;
            } else {
                let temp = a[i];
                a.set(i, temp + 1);
                toggle = 0;
            }
        } else {
            if toggle == 0 {
                let temp = a[i];
                a.set(i, temp - 1);
                toggle = 1;
            } else {
                let temp = a[i];
                a.set(i, temp - 1);
                toggle = 0;
            }
        }
        i = i + 1;
    }

    i = 0;
    toggle = 0;
    while (i < N as usize) {
        if toggle == 0 {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
            toggle = 1;
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
            toggle = 0;
        }
        i = i + 1;
    }
}

} // verus!
