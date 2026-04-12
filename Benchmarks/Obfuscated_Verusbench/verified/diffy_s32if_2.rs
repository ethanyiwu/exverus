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
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut tracker: usize = 0;
    let mut i: usize = 0;
    while i < N
        invariant
            forall|k: int| 0 <= k < i as int ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 1);
        tracker = tracker.wrapping_add(i);
        i += 1;
    }

    i = 0;
    while i < N
        invariant
            forall|k: int| 0 <= k < i as int ==> a[k] == 4,
            forall|k: int| i as int <= k < N as int ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        let current = a[i];
        if current == 1 {
            a.set(i, current + 3);
        } else {
            a.set(i, current - 1);
        }
        tracker = tracker.wrapping_sub(i);
        i += 1;
    }

    i = 0;
    let mut phantom: usize = 0;
    while i < N
        invariant
            i <= N,
            forall|k: int| 0 <= k < N as int ==> a[k] == 4,
            a.len() == N,
            sum[0] == 4 * (i as int),
            sum.len() == 1,
            N < 1000,
        decreases N - i,
    {
        let current = a[i];
        if current == 4 {
            let temp = sum[0];
            sum.set(0, temp + current);
        } else {
            let temp = sum[0];
            sum.set(0, temp + 0);
            phantom = phantom + 1;
        }
        tracker = tracker.wrapping_add(i);
        i += 1;
    }
}

} // verus!
