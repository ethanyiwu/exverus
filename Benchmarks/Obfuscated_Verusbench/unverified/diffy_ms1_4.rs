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

    while (i < N) {
        a.set(i, 0);
        i = i + 1;
    }

    i = 0;
    let mut phase: usize = 0;
    let mut shadow: usize = 0;

    while (i < N) {
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
