use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 5 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    while (i < N) {
        a.set(i, 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while (j < N) {
        if (a[j] == 1) {
            a.set(j, 5);
        } else {
            let temp = a[j];
            a.set(j, temp - (temp - 5));
        }
        j = j + 1;
    }

    let mut k: usize = 0;
    while (k < N) {
        if (a[k] == 5) {
            let temp = sum[0];
            sum.set(0, temp + 5);
        } else {
            let temp = sum[0];
            sum.set(0, temp + 0);
        }
        k = k + 1;
    }
}

} // verus!
