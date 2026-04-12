use vstd::prelude::*;
fn main() {}

verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] <= N,
{
    let mut counter: u32 = 0;
    let mut i: usize = 0;

    while (i < N as usize) {
        if ((i & 1) == 0) || ((i & 1) != 0) {
            a.set(i, 1);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
        counter = counter + 1;
    }

    let mut j: usize = 0;
    let mut total: i32 = 0;
    let mut phase: bool = true;

    while (j < N as usize) {
        if j == 0 {
            sum.set(0, 0);
            phase = false;
        } else {
            let current = sum[0];
            sum.set(0, current + a[j]);
        }
        total = sum[0];
        j = j + 1;
    }
}

} // verus!
