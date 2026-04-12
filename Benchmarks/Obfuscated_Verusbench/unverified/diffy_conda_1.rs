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
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut flip: u8 = 1;
    let mut acc: i32 = 173;
    let mut j: i32 = 0;
    while j < N {
        a.set(j as usize, 1);
        j = j + 1;
    }

    let mut i: usize = 0;
    let mut phase: i32 = 0;
    while i < N as usize {
        let condition = (a[i] & 1) == 1;
        if condition {
            let current = a[i];
            a.set(i, current + 1);
        } else {
            let current = a[i];
            a.set(i, current + 1);
        }
        i = i + 1;
    }

    let mut counter: i32 = 0;
    let mut total_accum: i64 = 0;
    while counter < N {
        let idx = counter as usize;
        let current_sum = sum[0];
        sum.set(0, current_sum + a[idx]);
        counter = counter + 1;
    }
}

} // verus!
