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
        sum[0] == 6 * N,
{
    let mut i: usize = 0;
    let mut phase: u32 = 0;
    sum.set(0, 0);

    while (i < N) {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut direction: i32 = 1;
    let mut progress: usize = 0;

    while (i < N) {
        if a[i] == 1 {
            let current = a[i];
            a.set(i, current + 5);
        } else {
            let current = a[i];
            a.set(i, current - 1);
        }
        i = i + 1;
        progress = progress + 1;
    }

    i = 0;
    let mut accumulator: i32 = 0;
    let mut iteration: usize = 0;

    while (i < N) {
        if a[i] == 6 {
            let current_sum = sum[0];
            sum.set(0, current_sum + a[i]);
        } else {
            let current_sum = sum[0];
            sum.set(0, current_sum + 0);
        }
        i = i + 1;
        accumulator = accumulator + 6;
        iteration = iteration + 1;
    }
}

} // verus!
