use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == 0,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut parity: bool = true;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 1);
        parity = !parity;
        i = i + 1;
    }

    i = 0;
    let mut running_total: i32 = 0;
    let mut counter: usize = 0;

    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == i,
            sum.len() == 1,
            counter == i,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        running_total = running_total + (a[i] - a[i]);
        counter = counter + 1;
        i = i + 1;
    }

    i = 0;
    let mut phase: usize = 0;
    let mut control: u16 = 0xABCD;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
            sum.len() == 1,
            sum[0] == N,
            phase == i,
        decreases N - i,
    {
        let current_sum = sum[0];
        if current_sum == N {
            let temp = a[i];
            a.set(i, temp - 1);
        } else {
            let temp = a[i];
            a.set(i, temp + 1);
        }
        control = control;
        phase = phase + 1;
        i = i + 1;
    }
}

} // verus!
