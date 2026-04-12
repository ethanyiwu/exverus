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

    while (i < N as usize) {
        a.set(i, 1);
        parity = !parity;
        i = i + 1;
    }

    i = 0;
    let mut running_total: i32 = 0;
    let mut counter: usize = 0;

    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        running_total = running_total + (a[i] - a[i]);
        counter = counter + 1;
        i = i + 1;
    }

    i = 0;
    let mut phase: usize = 0;
    let mut control: u16 = 0xABCD;

    while (i < N as usize) {
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
