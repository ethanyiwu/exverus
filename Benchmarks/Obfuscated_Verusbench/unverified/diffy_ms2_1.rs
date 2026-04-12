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

    while (i < N) {
        let val = (i & 1) as usize;
        a.set(i, val);
        phase = (phase + 1) % 2;
        i = i + 1;
    }

    sum.set(0, 0);
    let mut pos: usize = 0;
    let mut total: usize = 0;
    let mut offset: usize = 1;

    while (pos < N) {
        if a[pos] == 1 {
            total = total + 1;
            sum.set(0, total);
        }
        pos = pos + 1;
    }
}

} // verus!
