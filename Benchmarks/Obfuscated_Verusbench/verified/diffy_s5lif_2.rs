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
        sum[0] == 6 * N,
{
    let mut i: usize = 0;
    let mut alt_i: usize = 0;
    let mut phase: bool = true;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
            alt_i == i,
        decreases N - i,
    {
        if phase {
            a.set(i, 1);
        } else {
            a.set(i, 2 - 1);
        }
        i = i + 1;
        alt_i = alt_i + 1;
        phase = !phase;
    }

    i = 0;
    let mut toggle: bool = true;

    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 6,
            forall|j: int| i <= j < N ==> a[j] == 1,
            a.len() == N,
        decreases N - i,
    {
        let current = a[i];
        if (current == 1) == toggle {
            a.set(i, current + 5);
        } else {
            a.set(i, current + (6 - current));
        }
        i = i + 1;
        toggle = !toggle;
    }

    i = 0;
    let mut accum: i32 = 0;

    while (i < N as usize)
        invariant
            i <= N,
            forall|j: int| 0 <= j < N ==> a[j] == 6,
            sum[0] == 6 * i,
            sum.len() == 1,
            a.len() == N,
            N < 1000,
        decreases N - i,
    {
        let current_val = a[i];
        accum = accum + (current_val - current_val);
        let temp = sum[0];
        sum.set(0, temp + current_val);
        i = i + 1;
    }
}

} // verus!
