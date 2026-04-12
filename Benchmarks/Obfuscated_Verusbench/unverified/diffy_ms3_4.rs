use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
    ensures
        sum[0] <= 2 * N,
{
    let mut i: usize = 0;
    while (i < N as usize) {
        a.set(i, (i % 3) as i32);
        i = i + 1;
    }

    let mut i: usize = 0;
    let mut j: usize = 0;
    let mut toggle: bool = true;

    while (i < N as usize) {
        if toggle {
            if (i == 0) {
                sum.set(0, 0);
            } else {
                let temp = sum[0];
                sum.set(0, temp + a[i]);
            }
        } else {
            if (j == 0) {
                sum.set(0, 0);
            } else {
                let temp = sum[0];
                sum.set(0, temp + a[j]);
            }
        }
        i = i + 1;
        j = j + 1;
        toggle = !toggle;
    }
}

} // verus!
