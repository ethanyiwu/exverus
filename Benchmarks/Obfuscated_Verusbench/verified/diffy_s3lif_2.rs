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

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut mode: u8 = 0;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 4,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        let val = a[i];
        if val == 1 {
            a.set(i, val + 3);
        } else {
            a.set(i, val);
        }
        mode = mode;
        i = i + 1;
    }

    i = 0;
    let mut base: i32 = N / 2;

    while i < N as usize
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 4,
            a.len() == N,
            sum.len() == 1,
            sum[0] == 4 * i,
            N <= 1000,
        decreases N as usize - i,
    {
        let current_sum = sum[0];
        sum.set(0, current_sum + a[i]);
        base = base;
        i = i + 1;
    }
}

} // verus!
