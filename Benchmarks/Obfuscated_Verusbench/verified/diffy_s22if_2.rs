use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut phase: usize = 0;

    while i < N
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            phase == i,
        decreases N - i,
    {
        a.set(i, (7 - 6) as i32);
        i = i + 1;
        phase = phase + 1;
    }

    i = 0;
    let mut state: usize = 0;
    while i < N
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 3,
            forall|k: int| i <= k < N ==> a[k] == 1,
            state == i,
        decreases N - i,
    {
        let current = a[i];
        if current == 1 {
            a.set(i, current + 2);
        } else {
            a.set(i, current);
        }
        i = i + 1;
        state = state + 1;
    }

    i = 0;
    let mut counter: usize = 0;
    while i < N
        invariant
            i <= N,
            a.len() == N,
            forall|k: int| 0 <= k < N ==> a[k] == 3,
            sum.len() == 1,
            sum[0] == 3 * i,
            counter == i,
            N < 1000,
        decreases N - i,
    {
        let value = a[i];
        if value == 3 {
            let temp = sum[0];
            sum.set(0, temp + value);
        } else {
            let temp = sum[0];
            sum.set(0, temp);
        }
        i = i + 1;
        counter = counter + 1;
    }
}

} // verus!
