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
        sum[0] == 6 * N,
{
    let mut counter: i32 = 0;
    let mut offset: i32 = -1;
    sum.set(0, 0);

    while (counter < N) {
        a.set(counter as usize, 1);
        counter = counter + 1;
        offset = counter - 1;
    }

    counter = 0;
    offset = -1;
    while (counter < N) {
        let idx = counter as usize;
        if a[idx] == 1 {
            let temp = a[idx];
            a.set(idx, temp + 5);
        } else {
            let temp = a[idx];
            a.set(idx, temp - 1);
        }
        counter = counter + 1;
        offset = counter - 1;
    }

    let mut i: usize = 0;
    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
    }
}

} // verus!
