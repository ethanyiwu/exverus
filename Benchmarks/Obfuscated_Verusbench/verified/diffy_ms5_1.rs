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
        sum[0] <= 4 * N,
{
    let mut i: usize = 0;
    let mut track: i32 = 0;
    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == (k - 5 * (k / 5)) as i32,
            a.len() == N,
            track == i as i32,
        decreases (N as usize - i) as int,
    {
        a.set(i, (i - 5 * (i / 5)) as i32);
        i = i + 1;
        track = track + 1;
    }

    i = 0;
    let mut total: i32 = 0;
    let mut phase: bool = true;
    while !(i >= N as usize)
        invariant
            i <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == k % 5,
            a.len() == N,
            total <= 4 * i as i32,
            sum.len() == 1,
            total == if i > 0 {
                sum[0]
            } else {
                0
            },
            N < 1000,
        decreases (N as usize - i) as int,
    {
        if i == 0 {
            sum.set(0, 0);
            total = 0;
        } else {
            let temp = sum[0];
            let val = a[i];
            sum.set(0, temp + val);
            total = temp + val;
        }
        if phase {
            let _ = total.wrapping_mul(1);
        }
        phase = !phase;
        i = i + 1;
    }
}

} // verus!
