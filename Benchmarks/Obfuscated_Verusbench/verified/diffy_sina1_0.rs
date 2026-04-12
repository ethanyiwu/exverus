use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == N,
{
    let mut i: i32 = 0;
    let mut shadow: i32 = -1;
    sum.set(0, 0);

    while (i < N)
        invariant
            0 <= i <= N,
            sum.len() == 1,
            sum[0] == i,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + 1);
        i = i + 1;
        shadow = i - 1;
    }

    let mut j: i32 = 0;
    while (j < N)
        invariant
            0 <= j <= N,
            forall|k: int| 0 <= k < j ==> a[k] == sum[0],
            sum.len() == 1,
            a.len() == N,
        decreases N - j,
    {
        a.set(j as usize, sum[0]);
        j = j + 1;
    }
}

} // verus!
