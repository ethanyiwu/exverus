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
    let mut pos: usize = 0;
    let mut flip: u8 = 0;

    while (pos < N as usize)
        invariant
            forall|k: int| 0 <= k < pos ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            flip == 0 || flip == 1,
        decreases N as usize - pos,
    {
        let val = ((pos as i32) % 3) as i32;
        a.set(pos, val);

        flip = (flip + 1) % 2;
        pos = pos + 1;
    }

    let mut idx: i32 = -1;
    let mut processed: usize = 0;

    while (processed < N as usize)
        invariant
            processed <= N,
            idx == processed as i32 - 1,
            forall|k: int| 0 <= k < N ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            sum.len() == 1,
            processed > 0 ==> sum[0] <= 2 * processed,
            N < 1000,
        decreases N as usize - processed,
    {
        let current_idx = (idx + 1) as usize;

        if (processed == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[current_idx]);
        }

        processed = processed + 1;
        idx = idx + 1;
    }
}

} // verus!
