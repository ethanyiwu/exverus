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
        sum[0] == 5 * N,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    let mut phase: i32 = 0;
    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            phase == (i as i32) % 2,
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        i = i + 1;
        phase = (phase + 1) % 2;
    }

    i = 0;
    let mut direction: bool = true;
    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 5,
            forall|j: int| i <= j < N ==> a[j] == 1,
        decreases (N as usize) - i,
    {
        let current_val = a[i];
        let should_add = !(current_val != 1) && (current_val % 2 != 0);
        if should_add {
            a.set(i, current_val + 4);
        } else {
            a.set(i, current_val - 1);
        }
        i = i + 1;
        direction = !direction;
    }

    i = 0;
    let mut running_total: i32 = 0;
    while (i < N as usize)
        invariant
            i <= N as usize,
            a.len() == N,
            forall|j: int| 0 <= j < N ==> a[j] == 5,
            running_total == 5 * (i as i32),
            N < 1000,
        decreases (N as usize) - i,
    {
        let current_sum = running_total;
        running_total = current_sum + a[i];
        i = i + 1;
    }
    sum.set(0, running_total);
}

} // verus!
