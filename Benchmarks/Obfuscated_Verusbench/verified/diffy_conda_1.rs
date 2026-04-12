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
    while j < N
        invariant
            forall|k: int| 0 <= k < j ==> a[k] == 1,
            a.len() == N,
            j >= 0,
        decreases N - j,
    {
        a.set(j as usize, 1);
        j = j + 1;
    }

    let mut i: usize = 0;
    let mut phase: i32 = 0;
    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
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
    while counter < N
        invariant
            counter >= 0,
            counter <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            sum[0] == 2 * counter,
            sum.len() == 1,
            a.len() == N,
            N < 1000,
        decreases N - counter,
    {
        let idx = counter as usize;
        let current_sum = sum[0];
        sum.set(0, current_sum + a[idx]);
        counter = counter + 1;
    }
}

} // verus!
