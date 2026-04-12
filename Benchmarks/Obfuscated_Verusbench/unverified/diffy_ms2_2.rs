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
    let mut pattern: usize = 0;

    while i < N {
        a.set(i, (i % 2) as usize);
        pattern = (pattern + 1) % 2;
        i = i + 1;
    }

    i = 0;

    while i < N {
        if i == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
    }
}

} // verus!
