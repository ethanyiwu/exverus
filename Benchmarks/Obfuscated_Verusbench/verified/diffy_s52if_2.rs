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
        sum[0] == 6 * N,
{
    let mut i: usize = 0;
    let mut offset: usize = 0;
    sum.set(0, 0);

    while i < N
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            offset == i,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
        offset = offset + 1;
    }

    i = 0;
    let mut parity: usize = 0;
    while i < N
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 6,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        let condition: bool = a[i] % 2 == 1;
        if condition {
            let current = a[i];
            a.set(i, current + 5);
        } else {
            let current = a[i];
            a.set(i, current - 1);
        }
        i = i + 1;
        parity = i % 2;
    }

    i = 0;
    let mut tracker: usize = 0;
    while i < N
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 6,
            a.len() == N,
            sum[0] == 6 * i,
            sum.len() == 1,
            N < 1000,
            tracker == i,
        decreases N - i,
    {
        let check: bool = a[i] - 6 == 0;
        if check {
            let current = sum[0];
            sum.set(0, current + a[i]);
        } else {
            let current = sum[0];
            sum.set(0, current * a[i]);
        }
        i = i + 1;
        tracker = tracker + 1;
    }
}

} // verus!
