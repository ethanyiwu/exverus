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
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut tracker: i32 = 0;
    let mut i: usize = 0;
    while (i < N)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 1,
        decreases N - i,
    {
        tracker = tracker.wrapping_add(1);
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    while (i < N)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            forall|k: int| i <= k < N ==> a[k] == 1,
        decreases N - i,
    {
        let val = a[i];
        let adjustment: i32 = if val % 2 == 1 {
            1
        } else {
            -1
        };
        a.set(i, val.wrapping_add(adjustment));
        i = i + 1;
    }

    i = 0;
    while (i < N)
        invariant
            i <= N,
            a.len() == N,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            sum.len() == 1,
            sum[0] == 2 * i,
            N < 1000,
        decreases N - i,
    {
        let val = a[i];
        let addition: i32 = if val % 2 == 0 {
            val
        } else {
            0
        };
        let temp = sum[0];
        sum.set(0, temp.wrapping_add(addition));
        i = i + 1;
    }
}

} // verus!
