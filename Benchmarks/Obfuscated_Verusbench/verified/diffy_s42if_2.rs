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
    while (i < N)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while (j < N)
        invariant
            forall|k: int| 0 <= k < j ==> a[k] == 5,
            forall|k: int| j <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N - j,
    {
        if (a[j] == 1) {
            a.set(j, 5);
        } else {
            let temp = a[j];
            a.set(j, temp - (temp - 5));
        }
        j = j + 1;
    }

    let mut k: usize = 0;
    while (k < N)
        invariant
            k <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 5,
            a.len() == N,
            sum[0] == 5 * k,
            sum.len() == 1,
            N < 1000,
        decreases N - k,
    {
        if (a[k] == 5) {
            let temp = sum[0];
            sum.set(0, temp + 5);
        } else {
            let temp = sum[0];
            sum.set(0, temp + 0);
        }
        k = k + 1;
    }
}

} // verus!
