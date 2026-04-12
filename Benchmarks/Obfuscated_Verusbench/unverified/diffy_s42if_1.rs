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
    let mut pattern: usize = 0;

    while (i < N) {
        a.set(i, 1);
        pattern = 1 - pattern;
        i = i + 1;
    }

    i = 0;
    let mut shift: usize = 0;

    while (i < N) {
        if (a[i] == 1) {
            let temp = a[i];
            a.set(i, temp + 4);
            shift = (shift + 1) % 4;
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
            shift = (shift + 3) % 4;
        }
        i = i + 1;
    }

    i = 0;
    let mut counter: usize = 0;

    while (i < N) {
        if (a[i] == 5) {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
            counter = (counter + 1) % 8;
        } else {
            let temp = sum[0];
            sum.set(0, temp + 0);
            counter = (counter + 7) % 8;
        }
        i = i + 1;
    }
}

} // verus!
