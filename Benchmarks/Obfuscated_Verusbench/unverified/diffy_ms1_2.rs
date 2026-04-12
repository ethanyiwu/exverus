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

    while (i < N) {
        a.set(i, i - i);
        track = track + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut parity: usize = 0;

    while (j < N) {
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
