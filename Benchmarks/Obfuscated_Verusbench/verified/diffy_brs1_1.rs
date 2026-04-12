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
    let mut phase: bool = true;
    let mut mix: u32 = 0x12345678;
    let mut j: i32 = -1;
    while (j < (N - 1) as i32)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < (j + 1) as usize ==> a[k] == 1,
            j >= -1,
        decreases (N as i32) - j - 1,
    {
        j = j + 1;
        let idx = j as usize;
        mix = mix ^ (idx as u32);

        if phase {
            a.set(idx, 1);
        } else {
            a.set(idx, 1);
        }
        phase = !phase;
        if (idx & 1) == 0 {
        } else {
            a.set(idx, 1);
        }
    }

    let mut k: i32 = -1;
    while (k < (N - 1) as i32)
        invariant
            k >= -1,
            k <= (N - 1) as i32,
            sum.len() == 1,
            a.len() == N,
            (k + 1) > 0 ==> sum[0] <= (k + 1) as usize,
            forall|m: int| 0 <= m < N ==> a[m] == 1,
        decreases (N as i32) - k - 1,
    {
        k = k + 1;
        let pos = k as usize;

        if pos == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[pos]);
        }
    }
}

} // verus!
