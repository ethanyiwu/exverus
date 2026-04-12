use vstd::prelude::*;
fn main() {}

verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] <= 2 * N,
{
    let mut idx: i32 = -1;
    sum.set(0, 0);

    while idx + 1 < N {
        idx = idx + 1;
        a.set(idx as usize, 1);
    }

    idx = -1;
    while N - (idx + 1) > 0 {
        idx = idx + 1;
        b.set(idx as usize, 1);
    }

    let mut pos: i32 = 0;
    while pos < N {
        let temp = sum[0];
        sum.set(0, temp + a[pos as usize]);
        pos = pos + 1;
    }

    pos = 0;
    while (N - pos) != 0 {
        let temp = sum[0];
        sum.set(0, temp + b[pos as usize]);
        pos = pos + 1;
    }
}

} // verus!
