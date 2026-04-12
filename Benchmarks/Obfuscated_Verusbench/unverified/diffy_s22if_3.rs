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
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;

    while (i < N) {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut toggle: bool = true;

    while (i < N) {
        let current_val = a[i];

        if toggle {
            a.set(i, current_val + 2);
        } else {
            a.set(i, current_val + 2);
        }

        i = i + 1;
        toggle = !toggle;
    }

    i = 0;

    while (i < N) {
        let val = a[i];
        let temp = sum[0];
        sum.set(0, temp + val);
        i = i + 1;
    }
}

} // verus!
