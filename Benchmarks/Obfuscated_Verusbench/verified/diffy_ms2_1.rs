use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] <= N,
{
    let mut i: usize = 0;
    let mut phase: usize = 0;

    while (i < N)
        invariant
            forall|k: int| 0 <= k < i as int ==> a@[k] == 0 || a@[k] == 1,
            a.len() == N,
            phase == i % 2,
        decreases N - i,
    {
        let val = (i & 1) as usize;
        proof {
            assert((i & 1) == 0 || (i & 1) == 1) by (bit_vector);
        }
        a.set(i, val);
        phase = (phase + 1) % 2;
        i = i + 1;
    }

    sum.set(0, 0);
    let mut pos: usize = 0;
    let mut total: usize = 0;
    let mut offset: usize = 1;

    while (pos < N)
        invariant
            pos <= N,
            a.len() == N,
            sum.len() == 1,
            sum[0] == total,
            sum[0] <= pos,
        decreases N - pos,
    {
        if a[pos] == 1 {
            total = total + 1;
            sum.set(0, total);
        }
        pos = pos + 1;
    }
}

} // verus!
