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
    let mut track: usize = 0;

    while (i < N)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0,
            a.len() == N,
            track == i,
        decreases N - i,
    {
        a.set(i, i - i);
        track = track + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut parity: usize = 0;

    while (j < N)
        invariant
            forall|k: int| 0 <= k < N ==> a[k] == 0,
            a.len() == N,
            sum.len() == 1,
            (j > 0) ==> (sum[0] == 0),
        decreases N - j,
    {
        if (j == 0) {
            sum.set(0, 0);
        } else {
            let current = sum[0];
            sum.set(0, current + a[j]);
        }
        parity = (j + 1) % 2;
        j = j + 1;
    }
}

} // verus!
