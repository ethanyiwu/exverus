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
        sum[0] == 5 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;

    while i < N
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    while i < N
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 5,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        let current = a[i];
        if (current % 2 == 1) && (current > 0) {
            a.set(i, current + 4);
        } else {
            a.set(i, current - 1);
        }
        i = i + 1;
    }

    i = 0;
    while i < N
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 5,
            a.len() == N,
            sum[0] == 5 * i,
            sum.len() == 1,
            N < 1000,
        decreases N - i,
    {
        let current_val = a[i];
        if current_val == 5 {
            let temp = sum[0];
            sum.set(0, temp + current_val);
        } else {
            let temp = sum[0];
            sum.set(0, temp * current_val);
        }
        i = i + 1;
    }
}

} // verus!
