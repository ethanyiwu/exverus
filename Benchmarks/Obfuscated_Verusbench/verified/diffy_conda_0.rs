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
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
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
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
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
    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            sum[0] == 2 * i,
            sum.len() == 1,
            a.len() == N,
            N < 1000,
        decreases N - i,
    {
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
