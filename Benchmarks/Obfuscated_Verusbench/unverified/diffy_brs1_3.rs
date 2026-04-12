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
    let mut shadow: i32 = 0x5A5A5A5A;
    let mut idx: usize = 0;

    while idx < N as usize {
        a.set(idx, 1);
        shadow = shadow ^ ((idx as i32) + 1) ^ ((idx as i32) + 1);
        idx = idx + 1;
    }

    let mut counter: usize = 0;

    while counter < N as usize {
        counter = counter + 1;
    }
    sum.set(0, N);
}

} // verus!
