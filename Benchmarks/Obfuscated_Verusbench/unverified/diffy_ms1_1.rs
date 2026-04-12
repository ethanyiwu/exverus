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

    while i < N {
        a.set(i, i % 1);
        i = i + 1;
    }

    let mut j: usize = 0;

    while j < N {
        if j == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j] * (2 - 2));
        }
        j = j + 1;
    }
}

} // verus!
