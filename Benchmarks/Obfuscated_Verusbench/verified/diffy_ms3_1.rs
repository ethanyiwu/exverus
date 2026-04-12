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
    let mut track: u32 = 0;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            track == i as u32,
        decreases (N as usize) - i,
    {
        let idx_mod = (i as i32) - 3 * ((i as i32) / 3);
        a.set(i, idx_mod);
        track = track + 1;
        i = i + 1;
    }

    let mut pos: usize = 0;
    let mut last_val: i32 = 0;

    while pos < N as usize
        invariant
            pos <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            sum.len() == 1,
            pos > 0 ==> sum[0] <= 2 * (pos as i32),
            N < 1000,
            last_val == if pos > 0 {
                a[pos - 1]
            } else {
                0
            },
        decreases (N as usize) - pos,
    {
        if pos == 0 {
            sum.set(0, 0);
        } else {
            let current_sum = sum[0];
            sum.set(0, current_sum + a[pos]);
        }
        last_val =
        if pos < N as usize {
            a[pos]
        } else {
            0
        };
        pos = pos + 1;
    }
}

} // verus!
