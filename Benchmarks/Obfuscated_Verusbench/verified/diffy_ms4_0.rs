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
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut offset: usize = N as usize;
    while i < N as usize
        invariant
            offset == N as usize - i,
            forall|k: int| 0 <= k < i ==> a[k] == (k % 4) as i32,
            a.len() == N,
        decreases offset,
    {
        a.set(i, (i % 4) as i32);
        i = i + 1;
        offset = offset - 1;
    }

    i = 0;
    let mut counter: i32 = -1;

    while i < N as usize
        invariant
            i <= N as usize,
            counter == i as i32 - 1,
            i > 0 ==> sum[0] <= 3 * i,
            sum.len() == 1,
            forall|k: int| 0 <= k < N ==> a[k] == (k % 4) as i32,
            a.len() == N,
            N < 1000,
        decreases N as usize - i,
    {
        if !(i != 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
        counter = counter + 1;
    }
}

} // verus!
