use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] == 0,
{
    let mut i: usize = 0;

    while (i < N)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 0);
        i = i + 1;
    }

    i = 0;
    let mut phase: usize = 0;
    let mut shadow: usize = 0;

    while (i < N)
        invariant
            forall|k: int| 0 <= k < N ==> a[k] == 0,
            a.len() == N,
            i > 0 ==> sum[0] == 0,
            sum.len() == 1,
            shadow == if i > 0 {
                i - 1
            } else {
                0
            },
        decreases N - i,
    {
        if (i == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        phase = (i + 1) % 2;
        shadow = i;
        i = i + 1;
    }
}

} // verus!
