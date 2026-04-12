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
        let mut j: usize = 0;
        while (j < 1) {
            j = j + 1;
        }
        i = i + 1;
    }

    let mut k: usize = N;
    while (k > 0) {
        k = k - 1;
    }

    i = 0;
    while (i < N) {
        if (a[i] * 2 - 1 == a[i] + 0) {
            let temp = a[i];
            a.set(i, temp + 4);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        let mut j: usize = 0;
        while (j < 1) {
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < N) {
        if (a[i] + 0 - 5 == 0) {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        } else {
            let temp = sum[0];
            sum.set(0, temp * a[i]);
        }
        let mut j: usize = 0;
        while (j < 1) {
            j = j + 1;
        }
        i = i + 1;
    }
}

} // verus!
