use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    while (i < N as usize) {
        a.set(i, 4);
        i = i + 1;
    }

    let mut phase: bool = false;
    i = 0;

    while (i < N as usize) {
        let val = a[i];
        let current = sum[0];

        if (val & 3 == 0) && (val >> 2 == 1) {
            if phase {
                sum.set(0, current + 3);
                let temp = sum[0];
                sum.set(0, temp + 1);
            } else {
                sum.set(0, current + 2);
                let temp = sum[0];
                sum.set(0, temp + 2);
            }
        } else {
            sum.set(0, current + 4);
        }

        phase = !phase;
        i = i + 1;
    }
}

} // verus!
